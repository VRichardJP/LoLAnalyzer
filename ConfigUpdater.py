#!/usr/bin/env python

# Update the working patch and champions list

import configparser
import os
from InterfaceAPI import InterfaceAPI

config = configparser.ConfigParser()
if os.path.isfile('config.ini'):
    config.read('config.ini')
    API_KEY = config['CONFIG']['api-key']
else:
    def validationInput(msg, validAns):
        while True:
            data = input(msg)
            if data.lower() in validAns:
                return data
            print('Incorrect value. Only', validAns, 'are accepted')

    config.add_section('CONFIG')
    config.add_section('LEAGUE')
    config.add_section('REGIONS')
    config.add_section('CHAMPIONS')

    print("No config file found. Let's set up a few parameters (you may change them anytime by manually editing config.ini).")
    API_KEY = input('API-KEY (https://developer.riotgames.com/): ')
    config['CONFIG']['api-key'] = API_KEY
    config['CONFIG']['database'] = input('Database location (eg C:\LoLAnalyzerDB): ')
    print('Leagues you want to download games from (y/n): ')
    config['LEAGUE']['challenger'] = 'yes' if validationInput('challenger: ', ['y','n']) == 'y' else 'no'
    config['LEAGUE']['master'] = 'yes' if validationInput('master: ', ['y', 'n']) == 'y' else 'no'
    config['LEAGUE']['diamond'] = 'yes' if validationInput('diamond: ', ['y', 'n']) == 'y' else 'no'
    config['LEAGUE']['platinum'] = 'yes' if validationInput('platinum: ', ['y', 'n']) == 'y' else 'no'
    config['LEAGUE']['gold'] = 'yes' if validationInput('gold: ', ['y', 'n']) == 'y' else 'no'
    config['LEAGUE']['silver'] = 'yes' if validationInput('silver: ', ['y', 'n']) == 'y' else 'no'
    config['LEAGUE']['bronze'] = 'yes' if validationInput('bronze: ', ['y', 'n']) == 'y' else 'no'
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
json_data = api.getData('https://euw1.api.riotgames.com/lol/static-data/v3/champions', data={'locale': 'en_US','dataById':'true'})
PATCH = json_data['version']
config['CONFIG']['patch'] = PATCH
CHAMPIONS = json_data['data']
for champ_id, champ_info in CHAMPIONS.items():
    config['CHAMPIONS'][champ_info['name'].replace('\'','_').replace('.','').replace(' ','_')] = champ_id

with open('config.ini', 'w') as configfile:
    config.write(configfile)

print('Update complete')