#!/usr/bin/env python

# Send requests while respecting rate_limit
# Return data as dict (API send json)
import configparser
import json
import requests
import sys
import time

DEBUG = False
OFFSET = 2  # To avoid error 429. Normally not necessary but its just a security
TIME_LIMIT_WAIT = 120  # If we still get an error 429, wait a little


# The scripts have different behaviour depending on the errors
# 403 -> stop everything (wrong api-key)
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

        self.rate_limits = {}
        self.count = {}
        self.last_reset = {}

    def getData(self, uri, data=None):
        # need to wait?
        for t in self.count:
            if self.count[t] >= self.rate_limits[t] - OFFSET:  # need a window reset
                waiting_time = t - (time.time() - self.last_reset[t])  # time left until the end of the window
                if waiting_time > 0:
                    print('Too many requests, waiting', waiting_time, file=sys.stderr)
                    time.sleep(waiting_time)
                    self.count[t] = 0
                    self.last_reset[t] = time.time()

        # Request & response
        uri += '?api_key=' + self.API_KEY
        if data:
            for key, value in data.items():
                uri += '&%s=%s' % (key, value)
        resp = requests.get(uri)
        for key in self.count: # updated right after with a precise value, but I don't know
            self.count[key] += 1

        # Set the time limits on the first call
        if not self.rate_limits and 'X-App-Rate-Limit' in resp.headers and 'X-App-Rate-Limit-Count' in resp.headers:
            for r in resp.headers['X-App-Rate-Limit'].split(','):
                [l, t] = r.split(':')
                self.rate_limits[int(t)] = int(l)
            for r in resp.headers['X-App-Rate-Limit-Count'].split(','):
                [c, t] = r.split(':')
                self.count[int(t)] = int(c)
                self.last_reset[int(t)] = time.time()

        # Update & Check time
        if 'X-App-Rate-Limit-Count' in resp.headers:  # otherwise it's not concerned by the time limit
            for r in resp.headers['X-App-Rate-Limit-Count'].split(','):  # we use the api value to be precise
                [c, t] = r.split(':')
                self.count[int(t)] = int(c)

        if resp.status_code != 200:
            # This means something went wrong.
            if resp.status_code == 403:
                raise ApiError403('API-KEY has EXPIRED. Please set the new one in config.ini (https://developer.riotgames.com/)')
            elif resp.status_code == 404:
                raise ApiError404('Error %d - GET %s' % (resp.status_code, uri))
            elif resp.status_code == 429:
                # wait a little to make sure we don't hit the limit
                print('Error 429, waiting', TIME_LIMIT_WAIT, file=sys.stderr)
                time.sleep(TIME_LIMIT_WAIT)
                raise ApiError429('Error %d - GET %s' % (resp.status_code, uri))
            raise ApiError('Error %d - GET %s' % (resp.status_code, uri))
        elif DEBUG:
            print(uri, file=sys.stderr)

        return json.loads(resp.content.decode('utf-8'))


if __name__ == '__main__':
    print('-- Testing InterfaceAPI --', file=sys.stderr)
    interfaceAPI = InterfaceAPI()
    while True:
        interfaceAPI.getData('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/RiotSchmick')
