import os
import pandas as pd
import sys

import Modes


def run(mode):
    print('-- Updating roles --')
    extracted_files = [f for f in os.listdir(mode.EXTRACTED_DIR)]
    champ_roles = [[champ, {'N': 0, 'T': 0, 'J': 0, 'M': 0, 'C': 0, 'S': 0}] for champ in mode.CHAMPIONS_LABEL]
    for file in extracted_files:
        print(file, file=sys.stderr)
        csv_file = os.path.join(mode.EXTRACTED_DIR, file)
        data = pd.read_csv(csv_file, names=mode.COLUMNS, skiprows=1)
        for [champ, role_count] in champ_roles:
            counted_roles = data['p_' + champ].value_counts()
            # noinspection PyCompatibility
            for (r, n) in counted_roles.iteritems():
                role_count[r] += n

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
        mode.config['ROLES'][role] = ','.join(ROLES[role])

    with open('config.ini', 'w') as configfile:
        mode.config.write(configfile)

if __name__ == '__main__':
    run(Modes.ABR_TJMCS_Mode())
