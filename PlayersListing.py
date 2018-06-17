# Collect for each region the list of players by league
# Strategy: we go through the list of all the known players and check their games
# As a starting list, we can take master/challenger players
import os

import multiprocessing
import time
import pickle

import sys
from pickle import PickleError

from InterfaceAPI import InterfaceAPI, ApiError403, ApiError
import Modes

MAX_DAYS = 1  # up to how many days we look up
# Note it's not important that we get every single player, since we only need one participant for each game
MAX_DEPTH = 1000 * (time.time() - 86400 * MAX_DAYS)
ATTEMPTS = 6
ATTEMPTS_WAIT = 300
SAVE_INTERVAL = 600  # save every 10 minutes
DATABASE_WAIT = 60  # if the database cannot be reached, wait


class PlayerListing:
    def __init__(self, database, leagues, region, fast=False):
        self.api = InterfaceAPI()
        self.database = database
        self.leagues = leagues
        self.region = region
        self.nextSave = time.time() + SAVE_INTERVAL
        from_scratch = True

        if not os.path.isdir(self.database):
            raise FileNotFoundError(self.database)

        if not os.path.isdir(os.path.join(self.database, 'player_listing', self.region)):
            os.makedirs(os.path.join(self.database, 'player_listing', self.region))

        if os.path.exists(os.path.join(database, 'player_listing', self.region, 'players')):
                self.players = pickle.load(open(os.path.join(database, 'player_listing', self.region, 'players'), 'rb'))
                for league in leagues:
                    if self.players[league]:
                        from_scratch = False
                        break

        else:
            self.players = {}
            for league in leagues:
                self.players[league] = []

        # to make sure we don't explore several time the same player/ games
        if os.path.exists(os.path.join(database, 'player_listing', self.region, 'exploredPlayers')):
            self.exploredPlayers = pickle.load(open(os.path.join(database, 'player_listing', self.region, 'exploredPlayers'), 'rb'))
        else:
            self.exploredPlayers = []
        if os.path.exists(os.path.join(database, 'player_listing', self.region, 'exploredGames')):
            self.exploredGames = pickle.load(open(os.path.join(database, 'player_listing', self.region, 'exploredGames'), 'rb'))
        else:
            self.exploredGames = []
        if os.path.exists(os.path.join(database, 'player_listing', self.region, 'to_explore')):
            self.to_explore = pickle.load(open(os.path.join(database, 'player_listing', self.region, 'to_explore'), 'rb'))
        else:
            self.to_explore = []
        if os.path.exists(os.path.join(database, 'player_listing', self.region, 'exploredLeagues')):
            self.exploredLeagues = pickle.load(open(os.path.join(database, 'player_listing', self.region, 'exploredLeagues'), 'rb'))
        else:
            self.exploredLeagues = []

        if from_scratch:
            print(region, 'first time exploration, checking challenger and master leagues', file=sys.stderr)
            # only the first time
            if fast:  # only the challenger and master league, no need to explore anything
                if 'challenger' in self.players:
                    challLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/challengerleagues/by-queue/RANKED_SOLO_5x5' % self.region)
                    for e in challLeague['entries']:
                        self.players['challenger'].append(int(e['playerOrTeamId']))
                if 'master' in self.players:
                    masterLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/masterleagues/by-queue/RANKED_SOLO_5x5' % self.region)
                    for e in masterLeague['entries']:
                        self.players['master'].append(int(e['playerOrTeamId']))
            else:
                challLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/challengerleagues/by-queue/RANKED_SOLO_5x5' % self.region)
                for e in challLeague['entries']:
                    self.to_explore.append(int(e['playerOrTeamId']))
                masterLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/masterleagues/by-queue/RANKED_SOLO_5x5' % self.region)
                for e in masterLeague['entries']:
                    self.to_explore.append(int(e['playerOrTeamId']))
                self.exploredPlayers = list(self.to_explore)

    def explore(self):
        print(self.region, len(self.to_explore), 'players left to explore', file=sys.stderr)
        while self.to_explore:
            if time.time() > self.nextSave:
                print(self.region, len(self.to_explore), 'players left to explore', file=sys.stderr)
                print(self.region, 'saving...', file=sys.stderr)
                self.save()
                self.nextSave = time.time() + SAVE_INTERVAL

            sumID = self.to_explore.pop(0)  # strongest players first
            try:
                accountID = self.api.getData('https://%s.api.riotgames.com/lol/summoner/v3/summoners/%s' % (self.region, sumID))['accountId']
                games = \
                    self.api.getData('https://%s.api.riotgames.com/lol/match/v3/matchlists/by-account/%s' % (self.region, accountID), {'queue': 420})[
                        'matches']
                playerLeagueList = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/leagues/by-summoner/%s' % (self.region, sumID))
            except ApiError403 as e:
                print(e, file=sys.stderr)
                return e
            except ApiError as e:
                print(e, file=sys.stderr)
                continue

            # we check that the summoner is in one of the leagues we want
            playerSoloQLeague = None
            for league in playerLeagueList:
                if league['queue'] == 'RANKED_SOLO_5x5':
                    playerSoloQLeague = league
                    break
            if not playerSoloQLeague:
                print('no soloQ rank: ', self.region, sumID)
                continue
            playerLeagueTier = playerSoloQLeague['tier'].lower()
            playerLeagueName = playerSoloQLeague['name']
            if playerLeagueTier not in self.leagues:
                print('refused tier:', self.region, sumID, playerLeagueTier)
                continue

            self.players[playerLeagueTier].append(sumID)
            print('added:', self.region, sumID, playerLeagueTier)

            # We add all the people in the same league for exploration
            if playerLeagueName not in self.exploredLeagues:
                self.exploredLeagues.append(playerLeagueName)
                print('new league found:', self.region, playerLeagueTier, playerLeagueName)
                for e in playerSoloQLeague['entries']:
                    sumID = int(e['playerOrTeamId'])
                    if sumID not in self.exploredPlayers:
                        self.to_explore.append(sumID)
                        self.exploredPlayers.append(sumID)

            # We have to explore some games to get to other leagues
            # We hope that at least 1 player of each league has played within the time window
            for game in games:  # from most recent to oldest
                # the same game can come up to 10 times, so it's better to not make useless API calls
                if game['gameId'] in self.exploredGames:
                    continue
                self.exploredGames.append(game['gameId'])
                gameID = str(game['gameId'])
                timestamp = game['timestamp']
                if timestamp < MAX_DEPTH:  # game is too old?
                    break

                try:
                    gameData = self.api.getData('https://%s.api.riotgames.com/lol/match/v3/matches/%s' % (self.region, gameID))
                except ApiError403 as e:
                    print(e, file=sys.stderr)
                    return e
                except ApiError as e:
                    print(e, file=sys.stderr)
                    continue

                # adding all the non explored players from the game
                for participant in gameData['participantIdentities']:
                    sumID = participant['player']['summonerId']
                    if sumID not in self.exploredPlayers:
                        self.to_explore.append(sumID)
                        self.exploredPlayers.append(sumID)

        return None  # everything explored

    def save(self):
        while True:
            if not os.path.isdir(self.database):
                print(self.region, 'cannot access the local database', file=sys.stderr)
                time.sleep(DATABASE_WAIT)
                continue

            try:
                pickle.dump(self.players, open(os.path.join(self.database, 'player_listing', self.region, 'players'), 'wb'))
                pickle.dump(self.exploredPlayers, open(os.path.join(self.database, 'player_listing', self.region, 'exploredPlayers'), 'wb'))
                pickle.dump(self.exploredLeagues, open(os.path.join(self.database, 'player_listing', self.region, 'exploredLeagues'), 'wb'))
                pickle.dump(self.exploredGames, open(os.path.join(self.database, 'player_listing', self.region, 'exploredGames'), 'wb'))
                pickle.dump(self.to_explore, open(os.path.join(self.database, 'player_listing', self.region, 'to_explore'), 'wb'))
            except (PickleError, FileNotFoundError) as e:
                print(e, file=sys.stderr)
                print(self.region, 'saving failed', file=sys.stderr)
                time.sleep(DATABASE_WAIT)
                continue
            break


def keepExploring(database, leagues, region, attempts=ATTEMPTS):
    print(region, 'starting player listing', file=sys.stderr)
    pl = None
    if list(set(leagues) - {'challenger', 'master'}):  # we check it is necessary to look for the leagues
        while True:
            if not pl:
                try:
                    pl = PlayerListing(database, leagues, region)
                except ApiError403 as e:
                    print('FATAL ERROR', region, e, file=sys.stderr)
                    break
                except ApiError as e:
                    print(e, file=sys.stderr)
                    attempts -= 1
                    if attempts <= 0:
                        print(region, 'initial connection failed. No more connection attempt.', file=sys.stderr)
                        break
                    print(region, 'initial connection failed. Retrying in {} minutes. Attempts left:'.format(ATTEMPTS_WAIT, attempts), file=sys.stderr)
                    time.sleep(ATTEMPTS_WAIT)
                    continue
                except (PickleError,  FileNotFoundError) as e:
                    print(e, file=sys.stderr)
                    print(region, 'cannot access the local database', file=sys.stderr)
                    time.sleep(DATABASE_WAIT)
                    continue

            try:
                e = pl.explore()
            except KeyError:  # appends sometime, looks like some data is corrupted
                continue
            if e is not None:
                print('FATAL ERROR', region, e, file=sys.stderr)
            else:
                print(region, 'all players explored downloaded', file=sys.stderr)
            break
    else:  # only master/challenger league
        while True:
            if not pl:
                try:
                    pl = PlayerListing(database, leagues, region, fast=True)
                except ApiError403 as e:
                    print('FATAL ERROR', region, e, file=sys.stderr)
                    break
                except ApiError as e:
                    print(e, file=sys.stderr)
                    attempts -= 1
                    if attempts <= 0:
                        print(region, 'initial connection failed. No more connection attempt.', file=sys.stderr)
                        break
                    print(region, 'initial connection failed. Retrying in {} minutes. Attempts left: {}'.format(ATTEMPTS_WAIT, attempts), file=sys.stderr)
                    time.sleep(ATTEMPTS_WAIT)
                    continue
                except (PickleError, FileNotFoundError) as e:
                    print(e, file=sys.stderr)
                    print(region, 'cannot access the local database', file=sys.stderr)
                    time.sleep(DATABASE_WAIT)
                    continue

            # No need to explore
            print(region, 'all players explored downloaded', file=sys.stderr)
            break

    # we finally save the players list
    if pl is not None:
        print(region, 'Saving players list', file=sys.stderr)
        pl.save()


def run(mode):
    assert isinstance(mode, Modes.Base_Mode), 'Unrecognized mode {}'.format(mode)

    keprocs = []
    for region in mode.REGIONS:
        keprocs.append(multiprocessing.Process(target=keepExploring, args=(mode.DATABASE, mode.LEAGUES, region)))
        keprocs[-1].start()

    for keproc in keprocs:
        keproc.join()

    print('-- Listing complete --')


if __name__ == '__main__':
    m = Modes.Base_Mode()
    run(m)
