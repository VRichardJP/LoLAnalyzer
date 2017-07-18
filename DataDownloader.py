#!/usr/bin/env python

# Download games from the Riot API from Challenger/Master players
import configparser
import multiprocessing
import os
import pickle
import random
import sys
import time

from InterfaceAPI import InterfaceAPI, ApiError, ApiError404, ApiError403


class DataDownloader:
    def __init__(self, database, patch, region, leagues):
        self.api = InterfaceAPI()
        self.database = database
        self.region = region
        self.patch = patch
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
                games = self.api.getData('https://%s.api.riotgames.com/lol/match/v3/matchlists/by-account/%s' % (self.region, accountID), {'queue': 420})['matches']
            except ApiError as e:
                print(e, file=sys.stderr)
                continue
            for game in games:  # from most recent to oldest
                gameID = str(game['gameId'])
                # Already downloaded ?
                if gameID in self.downloadedGames:
                    break
                try:
                    # TODO Possible improvement: It is not necessary to make the request since we have the timestamp: game['gameId']['timestamp']
                    # TODO The best way is to use the patch info from the games to estimate when each patch was out
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
                # Game too old ?
                # formatting both so we can compare
                gameVersion = gameData['gameVersion'].split('.')[:2]
                gameVersion = tuple(list(map(int, gameVersion)))
                patchVersion = tuple(list(map(int, self.patch.split('.'))))
                if gameVersion < patchVersion:  # too old history
                    break
                if gameVersion > patchVersion:  # too recent history
                    continue

                file_path = os.path.join(self.db, gameID)
                pickle.dump(gameData, open(file_path, 'wb'))

                self.downloadedGames.append(gameID)
                print(self.patch, self.region, gameID)
                with open(self.downloadedGamesPath, 'a+') as f:
                    f.write(gameID + '\n')
        return None  # No data left to download


def keepDownloading(database, patches, region, leagues):
    print('Starting data collection for', region, patches, file=sys.stderr)
    for patch in patches:
        dd = None
        while True:
            if not dd:
                try:
                    dd = DataDownloader(database, patch, region, leagues)
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


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    DATABASE = config['PARAMS']['database']
    PATCHES_TO_DOWNLOAD = config['PARAMS']['download_patches'].split(',')
    LEAGUES = {league: enabled == 'yes' for (league, enabled) in config['LEAGUES'].items()}
    REGIONS = config['REGIONS']
    kdprocs = []
    for region, enabled in REGIONS.items():
        if enabled == 'yes':
            kdprocs.append(multiprocessing.Process(target=keepDownloading, args=(DATABASE, PATCHES_TO_DOWNLOAD, region, LEAGUES)))
            kdprocs[-1].start()

    for kdproc in kdprocs:
        kdproc.join()

    print('-- Download complete --')
