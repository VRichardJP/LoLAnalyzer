#!/usr/bin/env python

# Send requests while respecting rate_limit
# Return data as dict (API send json)
import configparser
import json
import requests
import sys
import time


class ApiError(Exception):
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
        uri += '?api_key=' + self.API_KEY
        if data:
            for key, value in data.items():
                uri += '&%s=%s' % (key, value)
        resp = requests.get(uri)

        if resp.status_code != 200:
            # This means something went wrong.
            if resp.status_code == 403:
                raise ApiError('API-KEY has EXPIRED. Please set the new one in config.ini (https://developer.riotgames.com/)')
            raise ApiError('Error %d - GET %s' % (resp.status_code, uri))
        else:
            print(uri, file=sys.stderr)

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
            for t in self.count:
                if self.count[t] >= self.rate_limits[t]-1:  # need a window reset
                    waiting_time = t - (time.time() - self.last_reset[t])  # time left until the end of the window
                    if waiting_time > 0:
                        print('Too many requests, waiting', waiting_time, file=sys.stderr)
                        time.sleep(waiting_time)
                        self.count[t] = 0
                        self.last_reset[t] = time.time()

        return json.loads(resp.content.decode('utf-8'))


if __name__ == '__main__':
    interfaceAPI = InterfaceAPI()
    while True:
        interfaceAPI.getData('https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/RiotSchmick')
