# All script can be called from here

import multiprocessing

import ConfigUpdater
import DataDownloader
import DataExtractor
import Networks
import RoleUpdater
import DataProcessing
import DataShuffling
import Learner
import BestPicks

import Modes


# Running options
image = False
permutation = False  # not implemented
cpu = multiprocessing.cpu_count() - 1
shuffling_files = 37  # prime to maximize spreading
reshuffle = True

# Mode and Network
mode = Modes.BR_Mode(image, permutation)
network = Networks.DenseUniform(mode, 5, 256)

# Scripts to execute, comment useless ones
to_execute = [
    # 'ConfigUpdater',
    'DataDownloader',  # run on multiple cpu
    'DataExtractor',
    'RoleUpdater',
    'DataProcessing',  # run on multiple cpu
    'DataShuffling',
    'Learner',  # run on gpu
]


if __name__ == '__main__':
    if 'ConfigUpdater' in to_execute:
        ConfigUpdater.run()
    if 'DataDownloader' in to_execute:
        DataDownloader.run(mode)
    if 'DataExtractor' in to_execute:
        DataExtractor.run(mode)
    if 'RoleUpdater' in to_execute:
        RoleUpdater.run(mode)
    if 'DataProcessing' in to_execute:
        DataProcessing.run(mode, cpu)
    if 'DataShuffling' in to_execute:
        DataShuffling.run(mode, shuffling_files, reshuffle)
    if 'Learner' in to_execute:
        Learner.run(mode, network)

    # BestPicks.run(mode=mode, IMAGE=image, arch='Dense5', a_kwargs={'NN': 2048, 'training': False})
