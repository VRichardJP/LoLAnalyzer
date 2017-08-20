# Collect for each region the list of players by league
# Strategy: we go through the list of all the known players and check their games
# As a starting list, we can take master/challenger players
import os

import multiprocessing
import time
import pickle

import sys

from InterfaceAPI import InterfaceAPI, ApiError403, ApiError, ApiError404
import Modes

MAX_DEPTH = 1000*(time.time() - 86400 * 3)  # up to 1 week
ATTEMPTS = 3
SAVE = 100


class PlayerListing:
    def __init__(self, database, leagues, region, fast=False):
        self.api = InterfaceAPI()
        self.database = database
        self.leagues = leagues
        self.region = region

        if os.path.exists(os.path.join(database, '{}_players'.format(region))):
            self.players = pickle.load(open(os.path.join(database, '{}_players'.format(region)), 'rb'))
        else:
            self.players = {}
            for league in leagues:
                self.players[league] = []

        # to make sure we don't explore several time the same player/ games
        if os.path.exists(os.path.join(database, '{}_exploredPlayers'.format(region))):
            self.exploredPlayers = pickle.load(open(os.path.join(database, '{}_exploredPlayers'.format(region)), 'rb'))
        else:
            self.exploredPlayers = []
        if os.path.exists(os.path.join(database, '{}_exploredGames'.format(region))):
            self.exploredGames = pickle.load(open(os.path.join(database, '{}_exploredGames'.format(region)), 'rb'))
        else:
            self.exploredGames = []
        if os.path.exists(os.path.join(database, '{}_to_explore'.format(region))):
            self.to_explore = pickle.load(open(os.path.join(database, '{}_to_explore'.format(region)), 'rb'))
        else:
            self.to_explore = []

        self.counter = 0

        if fast:  # only the challenger and master league, no need to explore anything
            challLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/challengerleagues/by-queue/RANKED_SOLO_5x5' % region)
            for e in challLeague['entries']:
                self.players['challenger'].append(e['playerOrTeamId'])
            masterLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/masterleagues/by-queue/RANKED_SOLO_5x5' % self.region)
            for e in masterLeague['entries']:
                self.players['master'].append(e['playerOrTeamId'])
        else:
            challLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/challengerleagues/by-queue/RANKED_SOLO_5x5' % region)
            for e in challLeague['entries']:
                self.to_explore.append(e['playerOrTeamId'])
            masterLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/masterleagues/by-queue/RANKED_SOLO_5x5' % self.region)
            for e in masterLeague['entries']:
                self.to_explore.append(e['playerOrTeamId'])
            self.exploredPlayers.extend(self.to_explore)

    def explore(self):
        while self.to_explore:
            self.counter += 1
            if self.counter % SAVE == 0:
                print(self.region, len(self.to_explore), 'left to explore')
                print(self.region, 'saving...')
                self.save()

            sumID = self.to_explore.pop()  # lowest rank player, better chances to find new players
            try:
                accountID = self.api.getData('https://%s.api.riotgames.com/lol/summoner/v3/summoners/%s' % (self.region, sumID))['accountId']
                games = self.api.getData('https://%s.api.riotgames.com/lol/match/v3/matchlists/by-account/%s' % (self.region, accountID), {'queue': 420})['matches']
                playerLeagueList = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/leagues/by-summoner/%s' % (self.region, sumID))
            except ApiError403 as e:
                print(e, file=sys.stderr)
                return e
            except (ApiError, ConnectionError) as e:
                print(e, file=sys.stderr)
                continue

            # we check that the summoner is in one of the leagues we want
            playerLeague = None
            for league in playerLeagueList:
                if league['queue'] == 'RANKED_SOLO_5x5' and league['tier'].lower():
                    playerLeague = league['tier'].lower()
            if playerLeague not in self.leagues:
                print('refused:', self.region, sumID, playerLeague)
                continue
            self.players[playerLeague].append(sumID)
            print('added:', self.region, sumID, playerLeague)

            useful_games = 0
            for game in games:  # from most recent to oldest
                if game in self.exploredGames:
                    continue
                self.exploredGames.append(game)
                gameID = str(game['gameId'])
                timestamp = game['timestamp']
                if timestamp < MAX_DEPTH:  # game is too old?
                    break

                useful_games += 1
                try:
                    gameData = self.api.getData('https://%s.api.riotgames.com/lol/match/v3/matches/%s' % (self.region, gameID))
                except ApiError403 as e:
                    print(e, file=sys.stderr)
                    return e
                except ApiError404 as e:
                    print(e, file=sys.stderr)
                    break
                except (ApiError, ConnectionError) as e:
                    print(e, file=sys.stderr)
                    continue

                # adding all the non explored players from the game
                for participant in gameData['participantIdentities']:
                    sumID = participant['player']['summonerId']
                    if sumID not in self.exploredPlayers:
                        self.to_explore.append(sumID)
                        self.exploredPlayers.append(sumID)
            print(self.region, sumID, useful_games, 'useful games explored')

        return None  # everything explored

    def save(self):
        pickle.dump(self.players, open(os.path.join(self.database, '{}_players'.format(self.region)), 'wb'))
        pickle.dump(self.exploredPlayers, open(os.path.join(self.database, '{}_exploredPlayers'.format(self.region)), 'wb'))
        pickle.dump(self.exploredGames, open(os.path.join(self.database, '{}_exploredGames'.format(self.region)), 'wb'))
        pickle.dump(self.to_explore, open(os.path.join(self.database, '{}_to_explore'.format(self.region)), 'rb'))


def keepExploring(database, leagues, region, attempts=ATTEMPTS):
    print('Starting players listing for', region, file=sys.stderr)
    pl = None
    if list(set(leagues) - {'challenger', 'master'}):  # we check it is necessary to look for the leagues
        while True:
            if not pl:
                try:
                    pl = PlayerListing(database, leagues, region)
                except ApiError403 as e:
                    print('FATAL ERROR', region, e, file=sys.stderr)
                    break
                except (ApiError, ConnectionError) as e:
                    print(e, file=sys.stderr)
                    attempts -= 1
                    if attempts <= 0:
                        print(region, 'initial connection failed. End of connection attempts.', file=sys.stderr)
                        break
                    print(region, 'initial connection failed. Retrying in 5 minutes. Attempts left:', attempts, file=sys.stderr)
                    time.sleep(300)
                    continue

            e = pl.explore()
            if e is not None:
                print('FATAL ERROR', region, e, file=sys.stderr)
                break
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
                        print(region, 'initial connection failed. End of connection attempts.', file=sys.stderr)
                        break
                    print(region, 'initial connection failed. Retrying in 5 minutes. Attempts left:', attempts, file=sys.stderr)
                    time.sleep(300)
                    continue

            # No need to explore
            print(region, 'all players explored downloaded', file=sys.stderr)
            break

    # we finally save the players list
    if pl is not None:
        print(region, 'Saving players list')
        pl.save()
    print(region, 'Listing complete')


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
    run(Modes.Base_Mode())
