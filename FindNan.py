import configparser
import os

import pandas as pd

config = configparser.ConfigParser()
config.read('config.ini')
DATABASE = config['PARAMS']['database']
PATCHES = config['PARAMS']['patches'].split(',')
CHAMPIONS_LABEL = config['PARAMS']['sortedChamps'].split(',')
CHAMPIONS_STATUS = ['A', 'B', 'O', 'T', 'J', 'M', 'C', 'S']

dataFile = os.path.join(DATABASE, 'data_test.csv')

names = CHAMPIONS_LABEL[:]
names.append('patch')
names.append('win')
names.append('file')
dtype = {champ: str for champ in CHAMPIONS_LABEL}
dtype['patch'] = str
dtype['win'] = str
dtype['file'] = str
df = pd.read_csv(dataFile, dtype=str)
# df = pd.read_csv(dataFile, names=names, dtype=dtype).sample(frac=1).reset_index(drop=True)
print(len(df))
print(len(pd.isnull(df)))
print(pd.isnull(df).iloc[:10].to_string())
