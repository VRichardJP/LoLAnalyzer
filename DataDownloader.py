# Download games from the Riot API from Challenger/Master players
import configparser
import multiprocessing
import os
import pickle
import random
import sys
import time

from Modes import BaseMode
from multiprocessing import Manager

from InterfaceAPI import InterfaceAPI, ApiError, ApiError404, ApiError403


class DataDownloader:
    def __init__(self, database, patch, region, leagues, timestamped_patches):
        self.api = InterfaceAPI()
        self.database = database
        self.region = region
        self.patch = patch
        self.timestamped_patches = timestamped_patches
        self.db = os.path.join(self.database, 'patches', self.patch, self.region)
        if not os.path.exists(self.db):
            os.makedirs(self.db)

        downloadedFile_name = self.region + '.txt'
        self.downloadedGamesPath = os.path.join(self.database, 'patches', self.patch, downloadedFile_name)
        if os.path.isfile(self.downloadedGamesPath):
            with open(self.downloadedGamesPath, 'r') as f:
                self.downloadedGames = [x.strip() for x in f.readlines()]
        else:
            self.downloadedGames = []
        self.summonerIDs = []
        if leagues['challenger']:
            challLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/challengerleagues/by-queue/RANKED_SOLO_5x5' % self.region)
            for e in challLeague['entries']:
                self.summonerIDs.append(e['playerOrTeamId'])
        if leagues['master']:
            masterLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/masterleagues/by-queue/RANKED_SOLO_5x5' % self.region)
            for e in masterLeague['entries']:
                self.summonerIDs.append(e['playerOrTeamId'])
        if leagues['diamond']:
            print('WARNING: data dl for diamond players not implemented', file=sys.stderr)
            pass
        if leagues['platinum']:
            print('WARNING: data dl for platinum players not implemented', file=sys.stderr)
            pass
        if leagues['gold']:
            print('WARNING: data dl for gold players not implemented', file=sys.stderr)
            pass
        if leagues['silver']:
            print('WARNING: data dl for silver players not implemented', file=sys.stderr)
            pass
        if leagues['bronze']:
            print('WARNING: data dl for bronze players not implemented', file=sys.stderr)
            pass
        random.shuffle(self.summonerIDs)

    def downloadData(self):
        while self.summonerIDs:  # if the API in unavailable, or the sumID is unreachable for w/e reason, just take the skip to the next
            sumID = self.summonerIDs.pop()
            try:
                accountID = self.api.getData('https://%s.api.riotgames.com/lol/summoner/v3/summoners/%s' % (self.region, sumID))['accountId']
                games = \
                    self.api.getData('https://%s.api.riotgames.com/lol/match/v3/matchlists/by-account/%s' % (self.region, accountID), {'queue': 420})[
                        'matches']
            except ApiError403 as e:
                print(e, file=sys.stderr)
                return e
            except ApiError as e:
                print(e, file=sys.stderr)
                continue
            for game in games:  # from most recent to oldest
                gameID = str(game['gameId'])

                # Wrong timestamp?
                timestamp = game['timestamp']
                previous_patch = self.patch
                previous_patch = previous_patch.split('.')
                previous_patch[1] = str(int(previous_patch[1]) - 1)
                previous_patch = '.'.join(previous_patch)
                if previous_patch in self.timestamped_patches and self.timestamped_patches[previous_patch][1] > timestamp:  # game is too old
                    break  # all the next games are too old

                next_patch = self.patch
                next_patch = next_patch.split('.')
                next_patch[1] = str(int(next_patch[1]) + 1)
                next_patch = '.'.join(next_patch)
                if next_patch in self.timestamped_patches and self.timestamped_patches[next_patch][0] < timestamp:  # game is too recent
                    continue  # need to go further

                # Already downloaded ?
                if gameID in self.downloadedGames:
                    break

                try:
                    gameData = self.api.getData('https://%s.api.riotgames.com/lol/match/v3/matches/%s' % (self.region, gameID))
                except ApiError403 as e:
                    print(e, file=sys.stderr)
                    return e
                except ApiError404 as e:
                    print(e, file=sys.stderr)
                    break
                except ApiError as e:
                    print(e, file=sys.stderr)
                    continue

                # update timestamps: gameData['gameCreation'] == game['timestamp']
                gamePatch = '.'.join(gameData['gameVersion'].split('.')[:2])
                timestamp = gameData['gameCreation']
                if gamePatch not in self.timestamped_patches:
                    self.timestamped_patches[gamePatch] = [timestamp, timestamp]
                else:  # first seen and last seen
                    if self.timestamped_patches[gamePatch][0] > timestamp:
                        self.timestamped_patches[gamePatch][0] = timestamp
                    elif self.timestamped_patches[gamePatch][1] < timestamp:
                        self.timestamped_patches[gamePatch][1] = timestamp

                # Game too old ?
                # formatting both so we can compare
                gameVersion = gameData['gameVersion'].split('.')[:2]
                gameVersion = tuple(list(map(int, gameVersion)))
                patchVersion = tuple(list(map(int, self.patch.split('.'))))
                if gameVersion < patchVersion:  # too old history
                    break
                if gameVersion > patchVersion:  # too recent history
                    continue

                # saving game
                file_path = os.path.join(self.db, gameID)
                pickle.dump(gameData, open(file_path, 'wb'))
                self.downloadedGames.append(gameID)
                print(self.patch, self.region, gameID)
                with open(self.downloadedGamesPath, 'a+') as f:
                    f.write(gameID + '\n')
        return None  # No data left to download


def keepDownloading(database, patches, region, leagues, timestamped_patches):
    print('Starting data collection for', region, patches, file=sys.stderr)
    for patch in patches:
        dd = None
        while True:
            if not dd:
                try:
                    dd = DataDownloader(database, patch, region, leagues, timestamped_patches)
                except ApiError403 as e:
                    print('FATAL ERROR', patch, region, e, file=sys.stderr)
                    return
                except ApiError as e:
                    print(e, file=sys.stderr)
                    print(region, 'initial connection failed. Retrying in 10 minutes', file=sys.stderr)
                    time.sleep(600)
                    continue

            e = dd.downloadData()
            if e is not None:
                print('FATAL ERROR', patch, region, e, file=sys.stderr)
                return
            print(region, patch, 'all games downloaded', file=sys.stderr)
            break
    print(region, 'download complete')


def saveLastSeen(timestamped_patches, save_interval, end):
    cfg = configparser.ConfigParser()
    cfg.read('config.ini')
    last_save = time.time()
    while not end.is_set():
        if last_save + save_interval < time.time():
            # we save the dictionnary
            for key, value in timestamped_patches.items():
                cfg['PATCHES'][key] = ','.join(list(map(str, value)))
            with open('config.ini', 'w') as configfile:
                cfg.write(configfile)
                print('patch timestamps saved')
            last_save = time.time()
        time.sleep(1)
    # we save the final state of the dictionnary
    for key, value in timestamped_patches.items():
        cfg['PATCHES'][key] = ','.join(list(map(str, value)))
    with open('config.ini', 'w') as configfile:
        cfg.write(configfile)
        print('patch timestamps saved')


def run(mode):
    assert type(mode) == BaseMode, 'Unrecognized mode {}'.format(mode)

    manager = Manager()
    last_seen_from_patch = manager.dict()
    endUpdate = manager.Event()
    for key, value in mode.config['PATCHES'].items():
        last_seen_from_patch[key] = list(map(int, value.split(',')))  # first seen and last seen

    kdprocs = []
    for region, enabled in mode.REGIONS.items():
        if enabled == 'yes':
            kdprocs.append(
                multiprocessing.Process(target=keepDownloading,
                                        args=(mode.DATABASE, mode.PATCHES_TO_DOWNLOAD, region, mode.LEAGUES, last_seen_from_patch)))
            kdprocs[-1].start()

    slsproc = multiprocessing.Process(target=saveLastSeen, args=(last_seen_from_patch, 300, endUpdate))
    slsproc.start()

    for kdproc in kdprocs:
        kdproc.join()

    endUpdate.set()
    slsproc.join()

    endUpdate.set()

    print('-- Download complete --')


if __name__ == '__main__':
    run(BaseMode())
