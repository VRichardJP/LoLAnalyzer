# Send requests while respecting rate_limit
# Return data as dict (API send json)

from __future__ import print_function

import configparser
import json
import collections
import requests
import sys
import time

DEBUG = False
OFFSET = 1  # just a security to avoid error 429. Prevent also the first request from reaching the rate-limit (we have no way to check the rate limit but to request something)
TIME_LIMIT_WAIT = 120  # If we still get an error 429, wait for a reset. It's painful so it's better to not have to deal with this
BYPASS_FIRST_WAIT = False  # Warning: only use if you haven't used the script for a while and you know there has been a reset.

# The scripts have different behaviour depending on the errors
# 403 -> stop everything (wrong a pi-key)
# 404 -> usually a summoner is not found, just ignore it and analyze the next one
# 429 -> time limit error. I'm still wondering why this is happening, but w/e, if that happens we just wait  little.
# Any other -> just ignore current game and get the next one (we don't want the script to be stuck so we never ask twice the same information)
# It is highly possible that some games where missed during a first scan (because of a random error). Downloading games a second time will eventualy fix the problem (ony download new games)

class ApiError(Exception):
    pass


class ApiError429(ApiError):
    pass


class ApiError404(ApiError):
    pass


class ApiError403(ApiError):
    pass


class InterfaceAPI:
    def __init__(self, API_KEY=None):
        self.API_KEY = API_KEY
        if not self.API_KEY:  # from config.ini
            config = configparser.ConfigParser()
            config.read('config.ini')
            self.API_KEY = config['PARAMS']['api-key']
        self.resets = {}

    # TODO Rework, simply keep in memory the time of the Nth call
    # https://stackoverflow.com/questions/1931589/python-datatype-for-a-fixed-length-fifo

    def getData(self, uri, data=None):
        # need to wait?
        for t in self.resets:
            wait = self.resets[t][0] + t + OFFSET - time.time()
            if wait > 0:
                if DEBUG:
                    print('Too many requests - waiting for', wait, file=sys.stderr)
                time.sleep(wait)

        # Request & response
        uri += '?api_key=' + self.API_KEY
        if data:
            for key, value in data.items():
                uri += '&%s=%s' % (key, value)
        resp = requests.get(uri)

        # initialize time limits - only once
        if not self.resets and 'X-App-Rate-Limit' and 'X-App-Rate-Limit-Count' in resp.headers:
            # We synchronize with the API to make a fresh start
            # This will be a problem if we have too big time limits (ironic huh)
            wait = 0
            if not BYPASS_FIRST_WAIT:
                for r in resp.headers['X-App-Rate-Limit-Count'].split(','):  # we use the api value to be precise
                    [c, t] = list(map(int, r.split(':')))
                    wait = max(wait, t) if c > 1 else wait
            if wait:
                if DEBUG:
                    print('Initial synchronization - waiting for', wait, file=sys.stderr)
                time.sleep(wait)
            for r in resp.headers['X-App-Rate-Limit'].split(','):
                [l, t] = list(map(int, r.split(':')))
                self.resets[t] = collections.deque(l * [0], l)

        # update current state
        for t in self.resets:
            self.resets[t].append(time.time())

        if resp.status_code != 200:
            # This means something went wrong.
            if resp.status_code == 403:
                raise ApiError403('API-KEY has EXPIRED. Please set the new one in config.ini (https://developer.riotgames.com/)')
            elif resp.status_code == 404:
                raise ApiError404('Error %d - GET %s' % (resp.status_code, uri))
            elif resp.status_code == 429:
                # wait a little to make sure we don't hit the limit
                if DEBUG:
                    print('Error 429, waiting', TIME_LIMIT_WAIT, file=sys.stderr)
                time.sleep(TIME_LIMIT_WAIT)
                raise ApiError429('Error %d - GET %s' % (resp.status_code, uri))
            raise ApiError('Error %d - GET %s' % (resp.status_code, uri))

        if DEBUG:
            print(uri, file=sys.stderr)

        return json.loads(resp.content.decode('utf-8'))


def run():
    print('-- Testing InterfaceAPI --', file=sys.stderr)
    interfaceAPI = InterfaceAPI()
    while True:
        interfaceAPI.getData('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/RiotSchmick')


if __name__ == '__main__':
    run()