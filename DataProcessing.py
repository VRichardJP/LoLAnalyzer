import configparser
import numpy as np
import pandas as pd
import os


CHAMPIONS_SIZE = 150
PATCHES_SIZE = 150
INPUT_SIZE = CHAMPIONS_SIZE * 8 + PATCHES_SIZE
config = configparser.ConfigParser()
config.read('config.ini')
DATABASE = config['PARAMS']['database']
PATCHES = config['PARAMS']['patches'].replace('.', '_').split(',')
PATCHES.extend((PATCHES_SIZE-len(PATCHES))*[None])
CHAMPIONS_LABEL = config['PARAMS']['sortedChamps'].split(',')
# CHAMPIONS_LABEL.extend((CHAMPIONS_SIZE-len(CHAMPIONS_LABEL))*[None])
CHAMPIONS_STATUS = ['A', 'B', 'O', 'T', 'J', 'M', 'C', 'S']

np.set_printoptions(formatter={'float_kind': lambda x: "%.2f" % x}, linewidth=200)


class dataCollector:
    def __init__(self, dataFile, preprocessedFile, netType):
        if netType == 'Value':
            names = CHAMPIONS_LABEL[:]
            names.append('win')
            names.append('patch')
            names.append('file')
            dtype = {champ: str for champ in CHAMPIONS_LABEL}
            dtype['patch'] = str
            dtype['win'] = int
            dtype['file'] = str
            if os.path.isfile(preprocessedFile) :
                preprocessed_df = pd.read_csv(preprocessedFile)
            else:
                preprocessed_df = []

            df = pd.read_csv(dataFile, names=names, dtype=dtype, skiprows=1)

            for i in range(len(preprocessed_df), df.shape[0]):
                # data: win + champions status + patch
                row = df.iloc[i]
                row_data = list()
                row_data.append(row['win'])
                row_data.extend([1 if row[CHAMPIONS_LABEL[k]] == s else 0 for s in CHAMPIONS_STATUS for k in range(len(CHAMPIONS_LABEL))])
                row_data.extend([0 for s in CHAMPIONS_STATUS for k in range(CHAMPIONS_SIZE - len(CHAMPIONS_LABEL))])
                row_data.extend([1 if row['patch'] == PATCHES[k] else 0 for k in range(PATCHES_SIZE)])
                data = pd.DataFrame.from_records([row_data])
                data.to_csv(preprocessedFile, mode='a', header=False, index=False)
        else:
            raise Exception('unknown netType', netType)

if __name__ == '__main__':
    dataFile = os.path.join(DATABASE, 'data.csv')
    preprocessedFile = os.path.join(DATABASE, 'data_value.csv')
    netType = 'Value'
    dataCollector(dataFile, preprocessedFile, netType)

