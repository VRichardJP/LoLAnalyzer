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

MAX_DEPTH = int(time.time() - 86400 * 1)  # up to 1 day
ATTEMPTS = 3


class PlayerListing:
    def __init__(self, database, leagues, region):
        self.api = InterfaceAPI()
        self.database = database
        self.leagues = leagues
        self.region = region
        self.players = {}  # summoner ID
        self.exploredPlayers = []  # to make sure we don't explore several time the same player
        for league in leagues:
            self.players[league] = []
        self.to_explore = []

        # we start with the challenger and master league
        challLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/challengerleagues/by-queue/RANKED_SOLO_5x5' % region)
        for e in challLeague['entries']:
            self.players['challenger'].append(e['playerOrTeamId'])
            self.to_explore.append(e['playerOrTeamId'])
        masterLeague = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/masterleagues/by-queue/RANKED_SOLO_5x5' % self.region)
        for e in masterLeague['entries']:
            self.players['master'].append(e['playerOrTeamId'])
            self.to_explore.append(e['playerOrTeamId'])
        self.exploredPlayers.extend(self.to_explore)

    def explore(self):
        while self.to_explore:
            sumID = self.to_explore.pop(0)  # highest rank player
            try:
                accountID = self.api.getData('https://%s.api.riotgames.com/lol/summoner/v3/summoners/%s' % (self.region, sumID))['accountId']
                games = self.api.getData('https://%s.api.riotgames.com/lol/match/v3/matchlists/by-account/%s' % (self.region, accountID), {'queue': 420})['matches']
                leagueList = self.api.getData('https://%s.api.riotgames.com/lol/league/v3/leagues/by-summoner/%s' % (self.region, sumID))['accountId']
            except ApiError403 as e:
                print(e, file=sys.stderr)
                return e
            except ApiError as e:
                print(e, file=sys.stderr)
                continue

            # we check that the summoner is in one of the leagues we want
            playerLeague = None
            for league in leagueList:
                if league['queue'] == 'RANKED_SOLO_5x5' and league['tier'].lower():
                    playerLeague = league['tier'].lower()
            if playerLeague not in self.leagues:
                print(self.region, sumID, 'refused:', playerLeague)
                continue
            self.players[playerLeague].append(sumID)
            print(self.region, sumID, 'added:', playerLeague)

            for game in games:  # from most recent to oldest
                gameID = str(game['gameId'])
                timestamp = game['timestamp']
                if timestamp < MAX_DEPTH:  # game is too old?
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

                # adding all the non explored players from the game
                for participant in gameData['participantIdentities']:
                    sumID = participant['player']['summonerId']
                    if sumID not in self.exploredPlayers:
                        self.to_explore.append(sumID)
                        self.exploredPlayers.append(sumID)

        return None  # everything explored

    def save(self):
        for league in self.leagues:
            file = os.path.join(self.database, 'players_{}_{}'.format(self.region, league))
            pickle.dump(self.players[league], open(file, 'wb'))


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
                except ApiError as e:
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

    # we finally save the players list
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
    run(Modes.ABR_Mode())
