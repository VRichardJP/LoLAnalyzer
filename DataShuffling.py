# moving consecutive lines from the same file in different files
# it's not a real shuffle from random but it spreads the data as much as possible so its the same
import multiprocessing
from functools import partial

import pandas as pd
import os
import sys
import Modes
import shutil


def split_to_file(mode, df, nb_files, i):
    currentFile = os.path.join(mode.TRAINING_DIR, 'data_' + str(i + 1) + '.csv')
    print(currentFile)
    index = [k * nb_files + i for k in range(len(df) // nb_files) if k * nb_files + i < len(df)]
    data = df.iloc[index, :]
    data.to_csv(currentFile, mode='a', header=False, index=False)


def shuffling(mode, dataFile, nb_files, cpu):
    df = pd.read_csv(os.path.join(mode.PREPROCESSED_DIR, dataFile), header=None)
    pool = multiprocessing.Pool(processes=max(cpu//2, 1))  # I get MemoryError when running on too many proc, need to find where the leak is.
    fun = partial(split_to_file, mode, df, nb_files)
    pool.map(fun, range(nb_files), chunksize=1)
    pool.close()
    pool.join()
    print(dataFile, 'DONE', file=sys.stderr)


def validationInput(msg, validAns):
    while True:
        data = input(msg)
        if data.lower() in validAns:
            return data
        print('Incorrect value. Only', validAns, 'are accepted')


def run(mode, nb_files, keep_for_testing, cpu):
    if os.path.isdir(mode.TRAINING_DIR):
        print('WARNING PREVIOUS SHUFFLED DATA FOUND', file=sys.stderr)
        # validation is annoying
        # if validationInput('Do you want to reshuffle the data anyway (take a while)? (y/n)', ['y', 'n']) == 'n':
        #     return

        if not os.access(mode.TRAINING_DIR, os.W_OK):
            # Is the error an access error ?
            # noinspection PyUnresolvedReferences
            os.chmod(mode.TRAINING_DIR, os.stat.S_IWUSR)
        shutil.rmtree(mode.TRAINING_DIR)
    os.makedirs(mode.TRAINING_DIR)
    if not os.path.isdir(mode.TESTING_DIR):
        os.makedirs(mode.TESTING_DIR)

    # listing extracted files and sorting
    preprocessed_files = [f for f in os.listdir(mode.PREPROCESSED_DIR)]
    l = list(map(lambda x: int(x.replace('data_', '').replace('.csv', '')), preprocessed_files))
    l = sorted(range(len(l)), key=lambda k: l[k])
    preprocessed_files = [preprocessed_files[k] for k in l]

    for _ in range(keep_for_testing):
        testing_file = preprocessed_files.pop(0)  # take data away for testing
        # no need to shuffle since it's a test
        shutil.copyfile(os.path.join(mode.PREPROCESSED_DIR, testing_file), os.path.join(mode.TESTING_DIR, testing_file))

    for file in preprocessed_files:
        shuffling(mode, file, nb_files, cpu)

if __name__ == '__main__':
    run(Modes.ABR_TJMCS_Mode(['7.16', '7.17']), 53, 2, cpu=max(multiprocessing.cpu_count() - 1, 1))
