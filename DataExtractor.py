# Extract the useful data from game files (json)
# Append the usefull data to a csv file

from __future__ import print_function

import configparser
import pickle
import os
import sys
from collections import OrderedDict

import pandas as pd
from collections import Counter

def run():
    DATA_LINES = 100000
    config = configparser.ConfigParser()
    config.read('config.ini')
    DATABASE = config['PARAMS']['database']
    EXTRACTED_DIR = os.path.join(DATABASE, 'extracted')
    PATCHES = os.listdir(os.path.join(DATABASE, 'patches'))
    CHAMPIONS_ID = config['CHAMPIONS']  # need to convert id: str -> int
    CHAMPIONS_ID = OrderedDict([(champ_name, int(champ_id)) for (champ_name, champ_id) in CHAMPIONS_ID.items()])
    CHAMPIONS_LABEL = config['PARAMS']['sortedChamps'].split(',')
    regions_list = config['REGIONS']
    COLUMNS = [champ for champ in CHAMPIONS_LABEL]
    COLUMNS.append('patch')
    COLUMNS.append('team')
    COLUMNS.append('win')
    COLUMNS.append('file')

    extracted_file = os.path.join(DATABASE, 'extracted.txt')
    if os.path.isfile(extracted_file):
        with open(extracted_file, 'r') as f:
            extracted_list = [x.strip() for x in f.readlines()]
    else:
        extracted_list = []

    gamesPath = []
    for patch in PATCHES:
        for region, enabled in regions_list.items():
            if enabled == 'yes' and os.path.isdir(os.path.join(DATABASE, 'patches', patch, region)):
                gamesPath.extend(
                    [os.path.join(DATABASE, 'patches', patch, region, f) for f in os.listdir(os.path.join(DATABASE, 'patches', patch, region))])
    print('%d game files found' % len(gamesPath))
    gamesPath = list(set(gamesPath) - set(extracted_list))
    print('%d new games to extract' % len(gamesPath))


    # Champion state:
    # Available, Banned, Opponent, Top, Jungle, Middle, Carry, Support
    def getRoleIndex(lane, role):
        if lane == 'TOP' and role == 'SOLO':
            return 'T'
        elif lane == 'JUNGLE' and role == 'NONE':
            return 'J'
        elif lane == 'MIDDLE' and role == 'SOLO':
            return 'M'
        elif lane == 'BOTTOM' and role == 'DUO_CARRY':
            return 'C'
        elif lane == 'BOTTOM' and role == 'DUO_SUPPORT':
            return 'S'
        else:
            raise Exception(lane, role)


    if not os.path.isdir(EXTRACTED_DIR):
        os.makedirs(EXTRACTED_DIR)

    extracted_files = [f for f in os.listdir(EXTRACTED_DIR)]
    l = list(map(lambda x: int(x.replace('data_', '').replace('.csv', '')), extracted_files))
    l = sorted(range(len(l)), key=lambda k: l[k])
    extracted_files = [extracted_files[k] for k in l]

    if extracted_files:
        current_index = len(extracted_files)
        current_file = extracted_files[current_index - 1]
        csv_file = os.path.join(EXTRACTED_DIR, current_file)
        csv_index = len(pd.read_csv(csv_file, skiprows=1))
        print('lines', csv_index)
    else:
        current_index = 0
        current_file = ''
        csv_file = None
        csv_index = DATA_LINES

    for gamePath in gamesPath:
        raw_data = OrderedDict([(champ, []) for champ in CHAMPIONS_LABEL])
        raw_data['patch'] = []
        raw_data['team'] = []
        raw_data['win'] = []
        raw_data['file'] = []
        print(gamePath)
        game = pickle.load(open(gamePath, 'rb'))
        blueTeam = None
        redTeam = None
        bans = []
        game_patch = '_'.join(game['gameVersion'].split('.')[:2])

        if game['gameDuration'] < 300:
            print('FF afk', game['gameDuration'])
            with open(extracted_file, 'a+') as f:
                f.write(gamePath)
                f.write('\n')
            continue

        blueTeam = None
        redTeam = None
        for team in game['teams']:
            if team['teamId'] == 100:
                blueTeam = team
            elif team['teamId'] == 200:
                redTeam = team
            else:
                print('Unrecognized team %d' % team['teamId'], file=sys.stderr)
                with open(extracted_file, 'a+') as f:
                    f.write(gamePath)
                    f.write('\n')
                continue

            for ban in team['bans']:
                championId = ban['championId']
                if championId not in bans:
                    bans.append(championId)
        if not blueTeam or not redTeam:
            print('Teams are not recognized', file=sys.stderr)
            with open(extracted_file, 'a+') as f:
                f.write(gamePath)
                f.write('\n')
            continue

        # not sure what is written for voided games, so it's safer to check both
        # if we get something else than true/false or false/true we just ignore the file
        blueWin = blueTeam['win'] == 'Win'
        redWin = redTeam['win'] == 'Win'
        if not blueWin ^ redWin:
            print('No winner found', blueWin, redWin, file=sys.stderr)
            with open(extracted_file, 'a+') as f:
                f.write(gamePath)
                f.write('\n')
            continue

        participants = game['participants']

        # Blank, everything is available
        blueState = OrderedDict()
        redState = OrderedDict()
        blueState['team'] = 0
        redState['team'] = 1
        blueState['win'] = int(blueWin)
        redState['win'] = int(redWin)
        blueState['patch'] = game_patch
        redState['patch'] = game_patch
        blueState['file'] = os.path.basename(gamePath)
        redState['file'] = os.path.basename(gamePath)
        blueState.update([(champ_name, 'A') for champ_name in CHAMPIONS_LABEL])
        redState.update([(champ_name, 'A') for champ_name in CHAMPIONS_LABEL])
        for key, value in blueState.items():
            raw_data[key].append(value)
        for key, value in redState.items():
            raw_data[key].append(value)

        # Bans
        blueState = dict(blueState)  # don't forget to create a clean copy
        redState = dict(redState)  # ortherwise it will modify previous states
        for championId in bans:
            for champ_name, champ_id in CHAMPIONS_ID.items():
                if champ_id == championId:
                    blueState[champ_name] = 'B'
                    redState[champ_name] = 'B'
                    break
        for key, value in blueState.items():
            raw_data[key].append(value)
        for key, value in redState.items():
            raw_data[key].append(value)

        # Smart lane-role
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
                else:
                    raise Exception(p, lane)
        # need to find the support in both team
        b_doubleRole = Counter(b_roles.values()).most_common(1)[0][0]
        b_doublei = [i for i, r in b_roles.items() if r == b_doubleRole]
        if len(b_doublei) > 2:
            print('fucked up roles', b_roles)
            with open(extracted_file, 'a+') as f:
                f.write(gamePath)
                f.write('\n')
            continue
        if 'SUPPORT' in participants[b_doublei[0]]['timeline']['role']:
            b_roles[b_doublei[0]] = 'S'
        elif 'SUPPORT' in participants[b_doublei[1]]['timeline']['role']:
            b_roles[b_doublei[1]] = 'S'
        else:  # Last resort -> check cs
            if 'creepsPerMinDeltas' in participants[b_doublei[0]]['timeline']:
                if participants[b_doublei[0]]['timeline']['creepsPerMinDeltas']['0-10'] < participants[b_doublei[1]]['timeline']['creepsPerMinDeltas'][
                    '0-10']:
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
            print('fucked up roles', r_roles)
            with open(extracted_file, 'a+') as f:
                f.write(gamePath)
                f.write('\n')
            continue
        if 'SUPPORT' in participants[r_doublei[0]]['timeline']['role']:
            r_roles[r_doublei[0]] = 'S'
        elif 'SUPPORT' in participants[r_doublei[1]]['timeline']['role']:
            r_roles[r_doublei[1]] = 'S'
        else:  # Last resort -> check cs
            if 'creepsPerMinDeltas' in participants[r_doublei[0]]['timeline']:
                if participants[r_doublei[0]]['timeline']['creepsPerMinDeltas']['0-10'] < participants[r_doublei[1]]['timeline']['creepsPerMinDeltas'][
                    '0-10']:
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
        DRAFT_ORDER = [0, 5, 6, 1, 2, 7, 8, 3, 4, 9]
        for i in DRAFT_ORDER:
            blueState = dict(blueState)
            redState = dict(redState)
            bluePick = i < 5
            p = participants[i]
            championId = p['championId']
            for champ_name, champ_id in CHAMPIONS_ID.items():
                if champ_id == championId:
                    blueState[champ_name] = roles[i] if bluePick else 'O'
                    redState[champ_name] = 'O' if bluePick else roles[i]
                    break
            for key, value in blueState.items():
                raw_data[key].append(value)
            for key, value in redState.items():
                raw_data[key].append(value)

        df = pd.DataFrame(raw_data, columns=COLUMNS)
        if csv_index + len(df) < DATA_LINES:
            df.to_csv(csv_file, mode='a', header=False, index=False)
            csv_index += len(df)
        else:  # split the data in two: finish prev file and start another
            to_current = df.iloc[:DATA_LINES - csv_index]
            to_next = df.iloc[DATA_LINES - csv_index:]
            to_current.to_csv(csv_file, mode='a', header=False, index=False)
            # preparing new file
            current_index += 1
            current_file = 'data_' + str(current_index) + '.csv'
            csv_file = os.path.join(EXTRACTED_DIR, current_file)
            csv_index = 0
            to_next.to_csv(csv_file, mode='a', header=True, index=False)
            csv_index += len(to_next)

        # File fully explored
        with open(extracted_file, 'a+') as f:
            f.write(gamePath)
            f.write('\n')

    print('-- Updating roles --')
    extracted_files = [f for f in os.listdir(EXTRACTED_DIR)]
    champ_roles = [[champ, {'A': 0, 'B': 0, 'O': 0, 'T': 0, 'J': 0, 'M': 0, 'C': 0, 'S': 0}] for champ in CHAMPIONS_LABEL]
    for file in extracted_files:
        csv_file = os.path.join(EXTRACTED_DIR, file)
        data = pd.read_csv(csv_file, names=COLUMNS, skiprows=1)
        for [champ, role_count] in champ_roles:
            counted_roles = data[champ].value_counts()
            for (r, n) in counted_roles.iteritems():
                role_count[r] += n

    ROLES = {'Top': [], 'Jungle': [], 'Mid': [], 'Carry': [], 'Support': []}
    POSSIBLE_ROLES = ['Top', 'Jungle', 'Mid', 'Carry', 'Support']
    for [champ, role_count] in champ_roles:
        s = 0
        for role in POSSIBLE_ROLES:
            s += role_count[role[0]]
        role_ratio = {}
        for role in POSSIBLE_ROLES:
            role_ratio[role] = 0 if role[0] not in role_count else role_count[role[0]] / s
        rr = role_ratio.items()
        print(champ, sorted(rr, key=lambda t:t[1], reverse=True))
        for role in role_ratio:
            if role_ratio[role] > 0.1:
                ROLES[role].append(champ)

    for role in ROLES:
        config['ROLES'][role] = ','.join(ROLES[role])

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    print('-- Extraction complete --')

if __name__ == '__main__':
    run()