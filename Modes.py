# Define all the shared constants among the scripts

import configparser
import os
from collections import OrderedDict

MAX_PATCHES = 10  # after 10 patches we consider the data is too old


class Base_Mode:
    def __init__(self, learning_patches=None):
        if learning_patches is None:
            learning_patches = []

        # Downloader+
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.DATABASE = self.config['PARAMS']['database']
        self.PATCHES_TO_DOWNLOAD = self.config['PARAMS']['download_patches'].split(',')
        self.LEAGUES = [league for (league, enabled) in self.config['LEAGUES'].items() if enabled == 'yes']
        self.REGIONS = [region for (region, enabled) in self.config['REGIONS'].items() if enabled == 'yes']

        # Extractor+
        self.DATA_LINES = 100000
        self.GAME_FILES = os.listdir(os.path.join(self.DATABASE, 'patches'))
        self.CHAMPIONS_ID = OrderedDict([(champ_name, int(champ_id)) for (champ_name, champ_id) in self.config['CHAMPIONS'].items()])
        self.CHAMPIONS_LABEL = self.config['PARAMS']['sortedChamps'].split(',')

        # Processing+
        self.SAVE = 1000
        self.CHAMPIONS_SIZE = len(self.CHAMPIONS_LABEL)
        # self.PATCHES = list(map(lambda x: x.replace('.', '_'), os.listdir(os.path.join(self.DATABASE, 'patches'))))
        # self.PATCHES = sorted(self.PATCHES, key=lambda x: tuple(map(int, x.split('_'))))
        # self.PATCHES = self.PATCHES[-MAX_PATCHES:]
        # self.PATCHES.extend([None] * (MAX_PATCHES - len(self.PATCHES)))
        self.PATCHES = list(map(lambda x: x.replace('.', '_'), learning_patches))
        self.PATCHES_SIZE = len(self.PATCHES)
        self.CURRENT_PATCH = self.PATCHES_SIZE * [0]
        self.CURRENT_PATCH[-1] = 1  # Lastest patch
        self.OUTPUT_SIZE = 1

        # LEARNING+
        self.CKPT_DIR = os.path.join(self.DATABASE, 'models')

        # BESTPICKS+
        self.ROLES_CHAMP = self.config['ROLES']
        self.BP_ROLES = ['...', 'Top', 'Jungle', 'Mid', 'Carry', 'Support']
        self.BP_CHAMPIONS = ['...']
        self.BP_CHAMPIONS.extend(sorted(self.CHAMPIONS_LABEL))
        self.BP_TEAMS = ['...', 'Blue', 'Red']

        # data
        self.EXTRACTED_FILE = os.path.join(self.DATABASE, 'extracted.txt')  # shared among the implementations
        self.EXTRACTED_DIR = os.path.join(self.DATABASE, 'extracted')
        self.COLUMNS = []
        self.COLUMNS.extend('s_' + champ_name for champ_name in self.CHAMPIONS_LABEL)
        self.COLUMNS.extend('p_' + champ_name for champ_name in self.CHAMPIONS_LABEL)
        self.COLUMNS.append('patch')
        self.COLUMNS.append('win')  # blue team pov
        self.COLUMNS.append('file')  # makes easier to read data files
        self.DTYPE = {}
        self.DTYPE.update({'s_' + champ_name: str for champ_name in self.CHAMPIONS_LABEL})
        self.DTYPE.update({'p_' + champ_name: str for champ_name in self.CHAMPIONS_LABEL})
        self.DTYPE['patch'] = str
        self.DTYPE['win'] = int
        self.DTYPE['file'] = str

    def __str__(self):
        return 'Base'.format()

    def __repr__(self):
        return 'Base_Mode()'.format()


# The main mode. It contains all the information you can get from a draft
# Each champion status is caracterized by 2 values:
# Available, Blue, Red (status)
# Top, Jungle, Mid, Carry, Support (position)
class ABR_TJMCS_Mode(Base_Mode):
    def __init__(self, learning_patches=None):
        super().__init__(learning_patches)
        self.PREPROCESSED_DIR = os.path.join(self.DATABASE, 'data_ABR_TJMCS')
        self.TRAINING_DIR = os.path.join(self.DATABASE, 'training_ABR_TJMCS')
        self.TESTING_DIR = os.path.join(self.DATABASE, 'testing_ABR_TJMCS')

        self.CHAMPIONS_STATUS = 'ABR'
        self.CHAMPIONS_POSITION = 'TJMCS'
        self.INPUT_SIZE = len(self.CHAMPIONS_LABEL) * (len(self.CHAMPIONS_STATUS) + len(self.CHAMPIONS_POSITION)) + len(self.PATCHES)

    def row_data(self, state, with_output=True, current_patch=False):
        row_data = []
        row_data.extend([1 if state['s_' + self.CHAMPIONS_LABEL[k]] == s else 0 for s in self.CHAMPIONS_STATUS for k in range(self.CHAMPIONS_SIZE)])
        row_data.extend([1 if state['p_' + self.CHAMPIONS_LABEL[k]] == s else 0 for s in self.CHAMPIONS_POSITION for k in range(self.CHAMPIONS_SIZE)])
        if current_patch:
            row_data.extend(self.CURRENT_PATCH)
        else:
            row_data.extend([1 if state['patch'] == self.PATCHES[k] else 0 for k in range(self.PATCHES_SIZE)])
        if with_output:
            row_data.append(state['win'])
        return row_data

    def __str__(self):
        return 'ABR_TJMCS'

    def __repr__(self):
        return 'ABR_TJMCS_Mode()'


# Minimalist mode, without roles
class ABR_Mode(Base_Mode):
    def __init__(self, learning_patches=None):
        super().__init__(learning_patches)
        self.PREPROCESSED_DIR = os.path.join(self.DATABASE, 'data_ABR')
        self.TRAINING_DIR = os.path.join(self.DATABASE, 'training_ABR')
        self.TESTING_DIR = os.path.join(self.DATABASE, 'testing_ABR')

        self.CHAMPIONS_STATUS = 'ABR'
        self.INPUT_SIZE = len(self.CHAMPIONS_LABEL) * len(self.CHAMPIONS_STATUS) + len(self.PATCHES)

    def row_data(self, state, with_output=True, current_patch=False):
        row_data = []
        row_data.extend([1 if state['s_' + self.CHAMPIONS_LABEL[k]] == s else 0 for s in self.CHAMPIONS_STATUS for k in range(self.CHAMPIONS_SIZE)])
        if current_patch:
            row_data.extend(self.CURRENT_PATCH)
        else:
            row_data.extend([1 if state['patch'] == self.PATCHES[k] else 0 for k in range(self.PATCHES_SIZE)])
        if with_output:
            row_data.append(state['win'])
        return row_data

    def __str__(self):
        return 'ABR'

    def __repr__(self):
        return 'ABR_Mode()'
