
# moving consecutive lines from the same file in different files
# it's not a real shuffle but it spreads the data as much as possible

import configparser
import numpy as np
import pandas as pd
import os

config = configparser.ConfigParser()
config.read('config.ini')
DATABASE = config['PARAMS']['database']
PREPROCESSED_DIR = os.path.join(DATABASE, 'data')
SHUFFLED_DIR = os.path.join(DATABASE, 'shuffled')

if os.path.isdir(SHUFFLED_DIR):
    import shutil

    if not os.access(SHUFFLED_DIR, os.W_OK):
        # Is the error an access error ?
        os.chmod(SHUFFLED_DIR, os.stat.S_IWUSR)
    shutil.rmtree(SHUFFLED_DIR)
os.makedirs(SHUFFLED_DIR)


def shuffling(dataFile, nb_files):
    df = pd.read_csv(os.path.join(PREPROCESSED_DIR, dataFile), header=None)
    for i in range(nb_files):
        currentFile = os.path.join(SHUFFLED_DIR, 'data_' + str(i+1) + '.csv')
        print(currentFile)
        index = [k * nb_files + i for k in range(len(df)//nb_files) if k * nb_files + i < len(df)]
        data = df.iloc[index, :]
        data.to_csv(currentFile, mode='a', header=False, index=False)
    print(dataFile, 'DONE')


def processData(netType):
    if netType == 'Value':
        # listing extracted files and sorting
        preprocessed_files = [f for f in os.listdir(PREPROCESSED_DIR)]
        l = list(map(lambda x: int(x.replace('data_', '').replace('.csv', '')), preprocessed_files))
        l = sorted(range(len(l)), key=lambda k:l[k])
        preprocessed_files = [preprocessed_files[k] for k in l]
        nb_files = len(preprocessed_files)
        for file in preprocessed_files:
            shuffling(file, nb_files)
    else:
        raise Exception('unknown netType', netType)


if __name__ == '__main__':
    netType = 'Value'
    processData(netType)
