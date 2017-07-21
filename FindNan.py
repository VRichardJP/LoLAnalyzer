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
names.append('patch')
names.append('win')
names.append('file')
df = pd.read_csv(dataFile, names=names, skiprows=1).sample(frac=1).reset_index(drop=True)
print(len(pd.isnull(df)))
print(pd.isnull(df).iloc[:10].to_string())
