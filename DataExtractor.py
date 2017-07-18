#!/usr/bin/env python

# Extract the useful data from game files (json)
# Append the usefull data to a csv file
import configparser
import pickle
import csv
import os

import sys
from collections import Counter

config = configparser.ConfigParser()
config.read('config.ini')
DATABASE = config['PARAMS']['database']
PATCHES = os.listdir(os.path.join(DATABASE, 'patches'))
LEAGUES = {league: enabled == 'yes' for (league, enabled) in config['LEAGUES'].items()}
CHAMPIONS = config['CHAMPIONS']  # need to convert id: str -> int
CHAMPIONS = {champ_name: int(champ_id) for (champ_name, champ_id) in CHAMPIONS.items()}
regions_list = config['REGIONS']
gamesPath = []

extracted_file = os.path.join(DATABASE, 'extracted.txt')
if os.path.isfile(extracted_file):
    with open(extracted_file, 'r') as f:
        extracted_list = [x.strip() for x in f.readlines()]
else:
    extracted_list = []

for patch in PATCHES:
    for region, enabled in regions_list.items():
        if enabled == 'yes' and os.path.isdir(os.path.join(DATABASE, 'patches', patch, region)):
            gamesPath.extend([os.path.join(DATABASE, 'patches', patch, region, f) for f in os.listdir(os.path.join(DATABASE, 'patches', patch, region))])
    print('%d game files found for %s' % (len(gamesPath), patch))
    gamesPath = list(set(gamesPath) - set(extracted_list))
    print('%d new games to extract' % len(gamesPath))

    csv_file = os.path.join(DATABASE, 'data.csv')
    writeheader = not os.path.isfile(csv_file)
    fieldsnames = [champ_name for champ_name in CHAMPIONS]
    fieldsnames.append('win')
    fieldsnames.append('patch')
    fieldsnames.append('file')
    writer = csv.DictWriter(open(csv_file, 'a+'), fieldnames=fieldsnames)
    if writeheader:
        writer.writeheader()


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


    for gamePath in gamesPath:
        print(gamePath)
        game = pickle.load(open(gamePath, 'rb'))
        blueTeam = None
        redTeam = None
        bans = []

        if game['gameDuration'] < 300:
            print('FF afk', game['gameDuration'])
            with open(extracted_file, 'a+') as f:
                f.write(gamePath)
                f.write('\n')
            continue
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
        blueState = {}
        redState = {}
        blueState['win'] = int(blueWin)
        redState['win'] = int(blueWin)
        blueState['patch'] = patch
        redState['patch'] = patch
        blueState['file'] = os.path.basename(gamePath)
        redState['file'] = os.path.basename(gamePath)
        blueState = {champ_name: 'A' for champ_name in CHAMPIONS}
        redState = {champ_name: 'A' for champ_name in CHAMPIONS}
        writer.writerows((blueState, redState))

        # Bans
        blueState = dict(blueState)  # don't forget to create a clean copy
        redState = dict(redState)  # ortherwise it will modify previous states
        for championId in bans:
            for champ_name, champ_id in CHAMPIONS.items():
                if champ_id == championId:
                    blueState[champ_name] = 'B'
                    redState[champ_name] = 'B'
                    break
        writer.writerows((blueState, redState))

        # Smart lane-role
        b_roles = {}
        r_roles = {}

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
                if participants[b_doublei[0]]['timeline']['creepsPerMinDeltas']['0-10'] < participants[b_doublei[1]]['timeline']['creepsPerMinDeltas']['0-10']:
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
                if participants[r_doublei[0]]['timeline']['creepsPerMinDeltas']['0-10'] < participants[r_doublei[1]]['timeline']['creepsPerMinDeltas']['0-10']:
                    r_roles[r_doublei[0]] = 'S'
                else:
                    r_roles[r_doublei[1]] = 'S'
            else:
                if participants[r_doublei[0]]['stats']['totalMinionsKilled'] < participants[r_doublei[1]]['stats']['totalMinionsKilled']:
                    r_roles[r_doublei[0]] = 'S'
                else:
                    r_roles[r_doublei[1]] = 'S'

        roles = {}
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
            for champ_name, champ_id in CHAMPIONS.items():
                if champ_id == championId:
                    blueState[champ_name] = roles[i] if bluePick else 'O'
                    redState[champ_name] = 'O' if bluePick else roles[i]
                    break
            writer.writerows((blueState, redState))

        # File fully explored
        with open(extracted_file, 'a+') as f:
            f.write(gamePath)
            f.write('\n')

print('-- Extraction complete --')
