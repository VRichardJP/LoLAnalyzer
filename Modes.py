# Define all the shared constants among the scripts

import configparser
import os
from collections import OrderedDict


class Base_Mode:
    def __init__(self):
        # Downloader+
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.DATABASE = self.config['PARAMS']['database']
        self.PATCHES_TO_DOWNLOAD = self.config['PARAMS']['download_patches'].split(',')
        self.LEAGUES = {league: enabled == 'yes' for (league, enabled) in self.config['LEAGUES'].items()}
        self.REGIONS = self.config['REGIONS']

        # Extractor+
        self.DATA_LINES = 100000
        self.GAME_FILES = os.listdir(os.path.join(self.DATABASE, 'patches'))
        self.CHAMPIONS_ID = OrderedDict([(champ_name, int(champ_id)) for (champ_name, champ_id) in self.config['CHAMPIONS'].items()])
        self.CHAMPIONS_LABEL = self.config['PARAMS']['sortedChamps'].split(',')

        # Processing+
        self.SAVE = 1000
        self.PATCHES = list(map(lambda x: x.replace('.', '_'), os.listdir(os.path.join(self.DATABASE, 'patches'))))
        self.PATCHES = sorted(self.PATCHES, key=lambda x: tuple(map(int, x.split('_'))))
        self.CHAMPIONS_SIZE = len(self.CHAMPIONS_LABEL)
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

    def __str__(self):
        return 'Base'.format()

    def __repr__(self):
        return 'Base_Mode()'.format()


# The main mode. It contains all the information you can get from a draft
class ABOTJMCS_Mode(Base_Mode):
    def __init__(self):
        super().__init__()
        self.EXTRACTED_FILE = os.path.join(self.DATABASE, 'extracted_ABOTJMCS.txt')
        self.EXTRACTED_DIR = os.path.join(self.DATABASE, 'extracted_ABOTJMCS')
        self.PREPROCESSED_DIR = os.path.join(self.DATABASE, 'data_ABOTJMCS')
        self.TRAINING_DIR = os.path.join(self.DATABASE, 'training_ABOTJMCS')
        self.TESTING_DIR = os.path.join(self.DATABASE, 'testing_ABOTJMCS')

        self.COLUMNS = self.CHAMPIONS_LABEL[:]
        self.COLUMNS.append('patch')
        self.COLUMNS.append('team')
        self.COLUMNS.append('win')
        self.COLUMNS.append('file')
        self.DTYPE = {champ: str for champ in self.CHAMPIONS_LABEL}
        self.DTYPE['patch'] = str
        self.DTYPE['team'] = int
        self.DTYPE['win'] = int
        self.DTYPE['file'] = str
        self.CHAMPIONS_STATUS = ['A', 'B', 'O', 'T', 'J', 'M', 'C', 'S']
        self.INPUT_SIZE = len(self.CHAMPIONS_LABEL) * len(self.CHAMPIONS_STATUS) + len(self.PATCHES) + 1

    def row_data(self, state, with_output=True, current_patch=False):
        row_data = []
        row_data.extend([1 if state[self.CHAMPIONS_LABEL[k]] == s else 0 for s in self.CHAMPIONS_STATUS for k in range(self.CHAMPIONS_SIZE)])
        if current_patch:
            row_data.extend(self.CURRENT_PATCH)
        else:
            row_data.extend([1 if state['patch'] == self.PATCHES[k] else 0 for k in range(self.PATCHES_SIZE)])
        row_data.append(state['team'])
        if with_output:
            row_data.append(state['win'])
        return row_data

    @staticmethod
    def from_ABOTJMCS(c):
        return c

    def __str__(self):
        return 'ABOTJMCS'

    def __repr__(self):
        return 'ABOTJMCS_Mode()'


class ABOT_Mode(Base_Mode):
    def __init__(self):
        super().__init__()
        self.EXTRACTED_FILE = os.path.join(self.DATABASE, 'extracted_ABOT.txt')
        self.EXTRACTED_DIR = os.path.join(self.DATABASE, 'extracted_ABOT')
        self.PREPROCESSED_DIR = os.path.join(self.DATABASE, 'data_ABOT')
        self.TRAINING_DIR = os.path.join(self.DATABASE, 'training_ABOT')
        self.TESTING_DIR = os.path.join(self.DATABASE, 'testing_ABOT')

        self.COLUMNS = self.CHAMPIONS_LABEL[:]
        self.COLUMNS.append('patch')
        self.COLUMNS.append('team')
        self.COLUMNS.append('win')
        self.COLUMNS.append('file')
        self.DTYPE = {champ: str for champ in self.CHAMPIONS_LABEL}
        self.DTYPE['patch'] = str
        self.DTYPE['team'] = int
        self.DTYPE['win'] = int
        self.DTYPE['file'] = str
        self.CHAMPIONS_STATUS = ['A', 'B', 'O', 'T']
        self.INPUT_SIZE = len(self.CHAMPIONS_LABEL) * len(self.CHAMPIONS_STATUS) + len(self.PATCHES) + 1

    def row_data(self, state, with_output=True, current_patch=False):
        row_data = []
        row_data.extend([1 if state[self.CHAMPIONS_LABEL[k]] == s else 0 for s in self.CHAMPIONS_STATUS for k in range(self.CHAMPIONS_SIZE)])
        if current_patch:
            row_data.extend(self.CURRENT_PATCH)
        else:
            row_data.extend([1 if state['patch'] == self.PATCHES[k] else 0 for k in range(self.PATCHES_SIZE)])
        row_data.append(state['team'])
        if with_output:
            row_data.append(state['win'])
        return row_data

    @staticmethod
    def from_ABOTJMCS(c):
        if c in 'TJMCS':
            c = 'T'  # player's team
        return c

    def __str__(self):
        return 'ABOT'

    def __repr__(self):
        return 'ABOT_Mode()'


class BR_Mode(Base_Mode):
    def __init__(self):
        super().__init__()
        self.EXTRACTED_FILE = os.path.join(self.DATABASE, 'extracted_BR.txt')
        self.EXTRACTED_DIR = os.path.join(self.DATABASE, 'extracted_BR')
        self.PREPROCESSED_DIR = os.path.join(self.DATABASE, 'data_BR')
        self.TRAINING_DIR = os.path.join(self.DATABASE, 'training_BR')
        self.TESTING_DIR = os.path.join(self.DATABASE, 'testing_BR')

        self.COLUMNS = self.CHAMPIONS_LABEL[:]
        self.COLUMNS.append('patch')
        self.COLUMNS.append('win')
        self.COLUMNS.append('file')
        self.DTYPE = {champ: str for champ in self.CHAMPIONS_LABEL}
        self.DTYPE['patch'] = str
        self.DTYPE['win'] = int
        self.DTYPE['file'] = str
        self.CHAMPIONS_STATUS = ['B', 'R']
        self.INPUT_SIZE = len(self.CHAMPIONS_LABEL) * len(self.CHAMPIONS_STATUS) + len(self.PATCHES)

    def row_data(self, state, with_output=True, current_patch=False):
        row_data = []
        row_data.extend([1 if state[self.CHAMPIONS_LABEL[k]] == s else 0 for s in self.CHAMPIONS_STATUS for k in range(self.CHAMPIONS_SIZE)])
        if current_patch:
            row_data.extend(self.CURRENT_PATCH)
        else:
            row_data.extend([1 if state['patch'] == self.PATCHES[k] else 0 for k in range(self.PATCHES_SIZE)])
        if with_output:
            row_data.append(state['win'])
        return row_data

    @staticmethod
    def from_ABOTJMCS(c, blue_team):
        if c in 'TJMCS':
            c = 'B' if blue_team else 'R'
        elif c == 'O':
            c = 'R' if blue_team else 'B'
        else:
            c = 'N'
        return c

    def __str__(self):
        return 'BR'

    def __repr__(self):
        return 'BR_Mode()'
