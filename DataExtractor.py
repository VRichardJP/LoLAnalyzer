# Extract the useful data from game files (json)
# Append the useful data to a csv file

import pickle
import os
import queue
import sys
from collections import OrderedDict
import multiprocessing
from multiprocessing.managers import BaseManager, NamespaceProxy
import time
import Modes
import pandas as pd
from collections import Counter

CHUNK_SIZE = 100


def extracted_writer(extracted_file, q, stop):
    with open(extracted_file, 'a+') as f:
        while not stop.is_set():
            try:
                game_path = q.get(timeout=1)
            except queue.Empty:
                continue
            f.write(game_path)
            f.write('\n')
        print('Closing writer', file=sys.stderr)


class Extractor:
    def __init__(self, mode, extracted_files, current_index, rot_length, writing_q):
        self.mode = mode
        self.rot_length = rot_length
        self.writing_q = writing_q

        self.current_index = current_index
        if len(extracted_files) >= self.current_index > 0:  # the file already exist
            self.csv_file = os.path.join(mode.EXTRACTED_DIR, extracted_files[self.current_index - 1])
            self.csv_index = len(pd.read_csv(self.csv_file, skiprows=1))
            print(self.csv_file, 'lines', self.csv_index, file=sys.stderr)
        else:
            self.csv_file = None
            self.csv_index = mode.DATA_LINES


class ExManager(BaseManager):
    pass


class ExProxy(NamespaceProxy):
    _exposed_ = ('__getattribute__', '__setattr__', '__delattr__', 'b')

ExManager.register('Extractor', Extractor, ExProxy)


def run(mode, cpu):
    extracted_file = mode.EXTRACTED_FILE
    if os.path.isfile(extracted_file):
        with open(extracted_file, 'r') as f:
            extracted_list = [x.strip() for x in f.readlines()]
    else:
        extracted_list = []

    gamePaths = []
    for patch in mode.learning_patches:
        for region in mode.REGIONS:
            if os.path.isdir(os.path.join(mode.DATABASE, 'patches', patch, region)):
                gamePaths.extend(
                    [os.path.join(mode.DATABASE, 'patches', patch, region, f) for f in
                     os.listdir(os.path.join(mode.DATABASE, 'patches', patch, region))])
    print('%d game files found' % len(gamePaths), file=sys.stderr)
    gamePaths = list(set(gamePaths) - set(extracted_list))
    print('%d new games to extract' % len(gamePaths), file=sys.stderr)

    if not os.path.isdir(mode.EXTRACTED_DIR):
        os.makedirs(mode.EXTRACTED_DIR)

    extracted_files = [f for f in os.listdir(mode.EXTRACTED_DIR)]
    l = list(map(lambda x: int(x.replace('data_', '').replace('.csv', '')), extracted_files))
    l = sorted(range(len(l)), key=lambda k: l[k])
    extracted_files = [extracted_files[k] for k in l]

    # multiprocessing
    manager = multiprocessing.Manager()
    writing_q = manager.Queue()
    stop = manager.Event()

    writer = multiprocessing.Process(target=extracted_writer, args=(extracted_file, writing_q, stop))
    writer.start()

    ex_manager = ExManager()
    ex_manager.start()
    available_extractors = []
    running_extractors = []
    for i in range(cpu):
        current_index = len(extracted_files) - i
        # noinspection PyUnresolvedReferences
        available_extractors.append(ex_manager.Extractor(mode, extracted_files, current_index, cpu, writing_q))

    while gamePaths:
        # we work with chunks in order to save time (no need to hand over the extractor for every single game
        chunk = gamePaths[:CHUNK_SIZE]
        gamePaths = gamePaths[CHUNK_SIZE:]
        print(len(gamePaths), 'left', file=sys.stderr)

        while not available_extractors:  # wait until an extractor is available
            for p, ex in running_extractors:
                if p.is_alive():
                    continue
                available_extractors.append(ex)
                running_extractors.remove((p, ex))
            if not available_extractors:  # wait a bit
                time.sleep(0.001)

        # start a new job
        ex = available_extractors.pop()
        p = multiprocessing.Process(target=analyze_game, args=(ex, chunk,))
        running_extractors.append((p, ex))
        p.start()

    for p, ex in running_extractors:
        p.join()

    stop.set()
    writer.join()
    print('-- Extraction complete --')


def analyze_game(ex, gamePaths):
    for gamePath in gamePaths:
        raw_data = OrderedDict([('s_' + champ, []) for champ in ex.mode.CHAMPIONS_LABEL] + [('p_' + champ, []) for champ in ex.mode.CHAMPIONS_LABEL])
        raw_data['patch'] = []
        raw_data['win'] = []
        raw_data['file'] = []
        print(ex.csv_file, gamePath)
        game = pickle.load(open(gamePath, 'rb'))
        bans = []
        game_patch = '_'.join(game['gameVersion'].split('.')[:2])

        if game['gameDuration'] < 300:
            print(gamePath, 'FF afk', game['gameDuration'], file=sys.stderr)
            ex.writing_q.put(gamePath)
            continue

        blueTeam = None
        redTeam = None
        for team in game['teams']:
            if team['teamId'] == 100:
                blueTeam = team
            elif team['teamId'] == 200:
                redTeam = team
            else:
                print(gamePath, 'Unrecognized team %d' % team['teamId'], file=sys.stderr)
                break

            for ban in team['bans']:
                championId = ban['championId']
                if championId not in bans:
                    bans.append(championId)
        if not blueTeam or not redTeam:
            print(gamePath, 'Teams are not recognized', file=sys.stderr)
            ex.writing_q.put(gamePath)
            continue

        # not sure what is written for voided games, so it's safer to check both
        # if we get something else than true/false or false/true we just ignore the file
        blueWin = blueTeam['win'] == 'Win'
        redWin = redTeam['win'] == 'Win'
        if not blueWin ^ redWin:
            print(gamePath, 'No winner found', blueWin, redWin, file=sys.stderr)
            ex.writing_q.put(gamePath)
            continue
        participants = game['participants']

        # Blank, everything is available
        state = OrderedDict()
        state['win'] = int(blueWin)
        state['patch'] = game_patch
        state['file'] = os.path.basename(gamePath)
        state.update([('s_' + champ_name, 'A') for champ_name in ex.mode.CHAMPIONS_LABEL])  # Status
        state.update([('p_' + champ_name, 'N') for champ_name in ex.mode.CHAMPIONS_LABEL])  # Position

        for key, value in state.items():
            raw_data[key].append(value)

        # Bans
        state = OrderedDict(state)  # don't forget to create a clean copy
        for championId in bans:
            for champ_name, champ_id in ex.mode.CHAMPIONS_ID.items():
                if champ_id == championId:
                    state['s_' + champ_name] = 'N'  # None
                    break
        for key, value in state.items():
            raw_data[key].append(value)

        # Smart lane-role
        # The Api doesn't precisely give players role, so we have to deduce it
        b_roles = OrderedDict()
        r_roles = OrderedDict()

        for i in range(0, 10):
            p = participants[i]
            lane = p['timeline']['lane']
            if i < 5:
                if lane == 'TOP':
                    b_roles[i] = 'T'
                elif lane == 'JUNGLE':
                    b_roles[i] = 'J'
                elif lane == 'MIDDLE':
                    b_roles[i] = 'M'
                elif lane == 'BOTTOM':
                    b_roles[i] = 'C'
                elif lane == 'NONE':
                    b_roles[i] = '?' # Fill missing lane if possible
                else:
                    raise Exception(p, lane)
            else:
                if lane == 'TOP':
                    r_roles[i] = 'T'
                elif lane == 'JUNGLE':
                    r_roles[i] = 'J'
                elif lane == 'MIDDLE':
                    r_roles[i] = 'M'
                elif lane == 'BOTTOM':
                    r_roles[i] = 'C'
                elif lane == 'NONE':
                    r_roles[i] = '?' # Fill missing lane if possible
                else:
                    raise Exception(p, lane)

        # Fill missing role 'F'
        # target at this point is something like 'T', 'J', 'M', 'C', 'C'
        b_toFillCount = Counter(b_roles.values())['?']
        if b_toFillCount > 1:
            print(gamePath, 'fucked up roles', b_roles, file=sys.stderr)
            ex.writing_q.put(gamePath)
            continue
        elif b_toFillCount == 1:
            fill_index = list(b_roles.keys())[list(b_roles.values()).index('?')]
            possible_roles = ['T', 'J', 'M', 'C']  
            missing_roles = list(set(possible_roles)-set(b_roles.values()))
            if len(missing_roles) == 1:
                # non-bot role
                b_roles[fill_index] = missing_roles[0]
            elif len(missing_roles) == 0:
                # bot, whether it is support will be determined later
                b_roles[fill_index] = 'C'
            else:
                print(gamePath, 'fucked up roles', b_roles, file=sys.stderr)
                ex.writing_q.put(gamePath)
                continue
        r_toFillCount = Counter(r_roles.values())['?']
        if r_toFillCount > 1:
            print(gamePath, 'fucked up roles', r_roles, file=sys.stderr)
            ex.writing_q.put(gamePath)
            continue
        elif r_toFillCount == 1:
            fill_index = list(r_roles.keys())[list(r_roles.values()).index('?')]
            possible_roles = ['T', 'J', 'M', 'C']  
            missing_roles = list(set(possible_roles)-set(r_roles.values()))
            if len(missing_roles) == 1:
                # non-bot role
                r_roles[fill_index] = missing_roles[0]
            elif len(missing_roles) == 0:
                # bot, whether it is support will be determined later
                r_roles[fill_index] = 'C'
            else:
                print(gamePath, 'fucked up roles', r_roles, file=sys.stderr)
                ex.writing_q.put(gamePath)
                continue

        # need to find the support in both team
        # a lane will appear twice, most likely 'C'
        # the support will either be tagged as 'SUPPORT' or have a low cs count 
        b_doubleRole = Counter(b_roles.values()).most_common(1)[0][0]
        b_doublei = [i for i, r in b_roles.items() if r == b_doubleRole]
        if len(b_doublei) > 2:
            print(gamePath, 'fucked up roles', b_roles, file=sys.stderr)
            ex.writing_q.put(gamePath)
            continue
        if 'SUPPORT' in participants[b_doublei[0]]['timeline']['role']:
            b_roles[b_doublei[0]] = 'S'
        elif 'SUPPORT' in participants[b_doublei[1]]['timeline']['role']:
            b_roles[b_doublei[1]] = 'S'
        else:  # Last resort -> check cs
            if 'creepsPerMinDeltas' in participants[b_doublei[0]]['timeline']:
                if participants[b_doublei[0]]['timeline']['creepsPerMinDeltas']['0-10'] < \
                        participants[b_doublei[1]]['timeline']['creepsPerMinDeltas']['0-10']:
                    b_roles[b_doublei[0]] = 'S'
                else:
                    b_roles[b_doublei[1]] = 'S'
            else:
                if participants[b_doublei[0]]['stats']['totalMinionsKilled'] < participants[b_doublei[1]]['stats']['totalMinionsKilled']:
                    b_roles[b_doublei[0]] = 'S'
                else:
                    b_roles[b_doublei[1]] = 'S'
        r_doubleRole = Counter(r_roles.values()).most_common(1)[0][0]
        r_doublei = [i for i, r in r_roles.items() if r == r_doubleRole]
        if len(r_doublei) > 2:
            print(gamePath, 'fucked up roles', r_roles, file=sys.stderr)
            ex.writing_q.put(gamePath)
            continue
        if 'SUPPORT' in participants[r_doublei[0]]['timeline']['role']:
            r_roles[r_doublei[0]] = 'S'
        elif 'SUPPORT' in participants[r_doublei[1]]['timeline']['role']:
            r_roles[r_doublei[1]] = 'S'
        else:  # Last resort -> check cs
            if 'creepsPerMinDeltas' in participants[r_doublei[0]]['timeline']:
                if participants[r_doublei[0]]['timeline']['creepsPerMinDeltas']['0-10'] < \
                        participants[r_doublei[1]]['timeline']['creepsPerMinDeltas']['0-10']:
                    r_roles[r_doublei[0]] = 'S'
                else:
                    r_roles[r_doublei[1]] = 'S'
            else:
                if participants[r_doublei[0]]['stats']['totalMinionsKilled'] < participants[r_doublei[1]]['stats']['totalMinionsKilled']:
                    r_roles[r_doublei[0]] = 'S'
                else:
                    r_roles[r_doublei[1]] = 'S'

        roles = OrderedDict()
        roles.update(b_roles)
        roles.update(r_roles)
        # Draft
        DRAFT_ORDER = [0, 5, 6, 1, 2, 7, 8, 3, 4, 9]  # This is not exact. This order is not pick order but end-draft order: if some players
        # trade, this order is wrong. Unfortunatelly there is no way to know the real pick order. So we just assume people don't trade often and
        # that trading does not have a huge impact anyway.
        for i in DRAFT_ORDER:
            state = OrderedDict(state)
            bluePick = i < 5
            p = participants[i]
            championId = p['championId']
            for champ_name, champ_id in ex.mode.CHAMPIONS_ID.items():
                if champ_id == championId:
                    state['s_' + champ_name] = 'B' if bluePick else 'R'
                    state['p_' + champ_name] = roles[i]
                    break
            for key, value in state.items():
                raw_data[key].append(value)

        df = pd.DataFrame(raw_data, columns=ex.mode.COLUMNS)
        if ex.csv_index + len(df) < ex.mode.DATA_LINES:
            df.to_csv(ex.csv_file, mode='a', header=False, index=False)
            ex.csv_index += len(df)
        else:  # split the data in two: finish prev file and start another
            to_current = df.iloc[:ex.mode.DATA_LINES - ex.csv_index]
            to_next = df.iloc[ex.mode.DATA_LINES - ex.csv_index:]
            to_current.to_csv(ex.csv_file, mode='a', header=False, index=False)
            # preparing new file
            ex.current_index += ex.rot_length
            current_file = 'data_' + str(ex.current_index) + '.csv'
            ex.csv_file = os.path.join(ex.mode.EXTRACTED_DIR, current_file)
            ex.csv_index = 0
            to_next.to_csv(ex.csv_file, mode='a', header=True, index=False)
            ex.csv_index += len(to_next)

        # File fully explored
        ex.writing_q.put(gamePath)


if __name__ == '__main__':
    m = Modes.ABR_TJMCS_Mode(['7.16', '7.17'])
    run(m, max(multiprocessing.cpu_count() - 1, 1))
