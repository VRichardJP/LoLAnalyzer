import configparser
import os
from collections import OrderedDict
import pandas as pd

def run(MODE='ABOTJMCS'):
    if MODE != 'ABOTJMCS':
        print('RoleUpdater Only available in ABOTJMCS mode')
        return

    DATA_LINES = 100000
    config = configparser.ConfigParser()
    config.read('config.ini')
    DATABASE = config['PARAMS']['database']
    EXTRACTED_DIR = os.path.join(DATABASE, 'extracted')
    PATCHES = os.listdir(os.path.join(DATABASE, 'patches'))
    CHAMPIONS_ID = config['CHAMPIONS']  # need to convert id: str -> int
    CHAMPIONS_ID = OrderedDict([(champ_name, int(champ_id)) for (champ_name, champ_id) in CHAMPIONS_ID.items()])
    CHAMPIONS_LABEL = config['PARAMS']['sortedChamps'].split(',')
    regions_list = config['REGIONS']
    COLUMNS = [champ for champ in CHAMPIONS_LABEL]
    COLUMNS.append('patch')
    COLUMNS.append('team')
    COLUMNS.append('win')
    COLUMNS.append('file')

    print('-- Updating roles --')
    extracted_files = [f for f in os.listdir(EXTRACTED_DIR)]
    champ_roles = [[champ, {'A': 0, 'B': 0, 'O': 0, 'T': 0, 'J': 0, 'M': 0, 'C': 0, 'S': 0}] for champ in CHAMPIONS_LABEL]
    for file in extracted_files:
        csv_file = os.path.join(EXTRACTED_DIR, file)
        data = pd.read_csv(csv_file, names=COLUMNS, skiprows=1)
        for [champ, role_count] in champ_roles:
            counted_roles = data[champ].value_counts()
            for (r, n) in counted_roles.iteritems():
                role_count[r] += n

        if champ_roles['C'] == 0:
            raise Exception('The extracted data does not contain any info about roles, make sure extraction is made in ABOTJMCS mode')

    ROLES = {'Top': [], 'Jungle': [], 'Mid': [], 'Carry': [], 'Support': []}
    POSSIBLE_ROLES = ['Top', 'Jungle', 'Mid', 'Carry', 'Support']
    for [champ, role_count] in champ_roles:
        s = 0
        for role in POSSIBLE_ROLES:
            s += role_count[role[0]]
        role_ratio = {}
        for role in POSSIBLE_ROLES:
            role_ratio[role] = 0 if role[0] not in role_count else role_count[role[0]] / s
        rr = role_ratio.items()
        print(champ, sorted(rr, key=lambda t: t[1], reverse=True))
        for role in role_ratio:
            if role_ratio[role] > 0.1:
                ROLES[role].append(champ)

    for role in ROLES:
        config['ROLES'][role] = ','.join(ROLES[role])

    with open('config.ini', 'w') as configfile:
        config.write(configfile)

