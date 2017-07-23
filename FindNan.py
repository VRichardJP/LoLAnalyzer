import configparser
import os

import pandas as pd

config = configparser.ConfigParser()
config.read('config.ini')
DATABASE = config['PARAMS']['database']
PATCHES = config['PARAMS']['patches'].split(',')
CHAMPIONS_LABEL = config['PARAMS']['sortedChamps'].split(',')
CHAMPIONS_STATUS = ['A', 'B', 'O', 'T', 'J', 'M', 'C', 'S']

dataFile = os.path.join(DATABASE, 'data.csv')

names = CHAMPIONS_LABEL[:]
names.append('win')
names.append('patch')
names.append('file')
dtype = {champ: str for champ in CHAMPIONS_LABEL}
dtype['patch'] = str
dtype['win'] = int
dtype['file'] = str
df = pd.read_csv(dataFile, names=names, dtype=dtype, skiprows=1)
# print(df.iloc[:10].to_string())
# df = pd.read_csv(dataFile, names=names, dtype=dtype, skiprows=1).sample(frac=1).reset_index(drop=True)
# print(df.iloc[:10].to_string())

# print(len(df))
# print(pd.isnull(df).iloc[:10].to_string())
inds = pd.isnull(df).any(1).nonzero()[0]
print(inds)

