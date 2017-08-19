# Update the working patch and champions list

from __future__ import print_function

import configparser
import json
import os
import urllib.request
from datetime import datetime
from slugify import slugify
from collections import OrderedDict
from InterfaceAPI import InterfaceAPI


def run():
    config = configparser.ConfigParser()
    if os.path.isfile('config.ini'):
        config.read('config.ini')
        API_KEY = config['PARAMS']['api-key']
    else:
        def validationInput(msg, validAns):
            while True:
                ans = input(msg)
                if ans.lower() in validAns:
                    return ans
                print('Incorrect value. Only', validAns, 'are accepted')

        config.add_section('PARAMS')
        config.add_section('LEAGUES')
        config.add_section('REGIONS')
        config.add_section('PATCHES')
        config.add_section('CHAMPIONS')
        config.add_section('ROLES')

        print("No config file found. Let's set up a few parameters (you may change them anytime by manually editing config.ini).")
        API_KEY = input('API-KEY (https://developer.riotgames.com/): ')
        config['PARAMS']['api-key'] = API_KEY
        config['PARAMS']['database'] = input('Database location (eg. C:\LoLAnalyzerDB): ')
        print('Leagues you want to download games from (y/n): ')
        config['LEAGUES']['challenger'] = 'yes' if validationInput('challenger: ', ['y', 'n']) == 'y' else 'no'
        if config['LEAGUES']['challenger'] == 'yes':
            config['LEAGUES']['master'] = 'yes' if validationInput('master: ', ['y', 'n']) == 'y' else 'no'
        if config['LEAGUES']['master'] == 'yes':
            config['LEAGUES']['diamond'] = 'yes' if validationInput('diamond: ', ['y', 'n']) == 'y' else 'no'
        if config['LEAGUES']['diamond'] == 'yes':
            config['LEAGUES']['platinum'] = 'yes' if validationInput('platinum: ', ['y', 'n']) == 'y' else 'no'
        if config['LEAGUES']['platinum'] == 'yes':
            config['LEAGUES']['gold'] = 'yes' if validationInput('gold (not recommended): ', ['y', 'n']) == 'y' else 'no'
        if config['LEAGUES']['gold'] == 'yes':
            config['LEAGUES']['silver'] = 'yes' if validationInput('silver (not recommended): ', ['y', 'n']) == 'y' else 'no'
        if config['LEAGUES']['silver'] == 'yes':
            config['LEAGUES']['bronze'] = 'yes' if validationInput('bronze (not recommended): ', ['y', 'n']) == 'y' else 'no'
        print('Regions you want to download games from (the more the better) (y/n):')
        config['REGIONS']['ru'] = 'yes' if validationInput('ru: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['kr'] = 'yes' if validationInput('kr: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['br1'] = 'yes' if validationInput('br1: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['oc1'] = 'yes' if validationInput('oc1: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['jp1'] = 'yes' if validationInput('jp1: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['na1'] = 'yes' if validationInput('na1: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['eun1'] = 'yes' if validationInput('eun1: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['euw1'] = 'yes' if validationInput('euw1: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['tr1'] = 'yes' if validationInput('tr1: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['la1'] = 'yes' if validationInput('la1: ', ['y', 'n']) == 'y' else 'no'
        config['REGIONS']['la2'] = 'yes' if validationInput('la2: ', ['y', 'n']) == 'y' else 'no'

    # Update to current patch & champions list
    # euw1 is used as reference
    api = InterfaceAPI(API_KEY)
    PATCHES = api.getData('https://euw1.api.riotgames.com/lol/static-data/v3/versions')
    PATCHES = ['.'.join(s.split('.')[:2]) for s in reversed(PATCHES)]
    config['PARAMS']['download_patches'] = PATCHES[-1]
    print('Current patch set to:', config['PARAMS']['download_patches'])
    PATCHES = OrderedDict((x, True) for x in PATCHES).keys()
    config['PARAMS']['patches'] = ','.join(PATCHES)
    print('Patch list updated')
    json_data = api.getData('https://euw1.api.riotgames.com/lol/static-data/v3/champions', data={'locale': 'en_US', 'dataById': 'true'})
    CHAMPIONS = json_data['data']
    sortedChamps = []
    for champ_id, champ_info in CHAMPIONS.items():
        slugname = slugify(champ_info['name'], separator='')
        config['CHAMPIONS'][slugname] = champ_id
        sortedChamps.append(slugname)
    # We need to sort champions by release for the neural network
    # This is really important for the compatibility of the system over the patches
    # Unfortunately the API doesn't give this information, so we use: http://universe-meeps.leagueoflegends.com/v1/en_us/champion-browse/index.json
    response = urllib.request.urlopen('http://universe-meeps.leagueoflegends.com/v1/en_us/champion-browse/index.json')
    data = json.loads(response.read().decode())
    champ_date = {}
    for champ in data['champions']:
        date = champ['release-date']
        date = date[1:] if date[0] == ' ' else date  # solve a problem on annie
        date = date[:10]  # solve a problem on aatrox
        champ_date[slugify(champ['name'], separator='')] = datetime.strptime(date, '%Y-%m-%d')
    sortedChamps.sort(key=lambda x: (champ_date[x], x))  # sorted by date and then abc order (eg. annie/yi or xhaya/rakan)
    config['PARAMS']['sortedChamps'] = ','.join(sortedChamps)
    print('Champions list updated')

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

    print('-- Update complete --')

if __name__ == '__main__':
    run()
