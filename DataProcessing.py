# Pre-process the data according to a given pattern

from functools import partial
import numpy as np
import multiprocessing
import pandas as pd
import os
import Modes

np.set_printoptions(formatter={'float_kind': lambda x: "%.2f" % x}, linewidth=200)


def processing(mode, dataFile):
    currentFile = os.path.join(mode.PREPROCESSED_DIR, dataFile)
    if os.path.isfile(currentFile):
        preprocessed_df = pd.read_csv(currentFile, header=None)
    else:
        preprocessed_df = []
    df = pd.read_csv(os.path.join(mode.EXTRACTED_DIR, dataFile), names=mode.COLUMNS, dtype=mode.DTYPE, skiprows=1)
    print(currentFile, len(df) - len(preprocessed_df), "rows to analyze")
    data = pd.DataFrame(columns=range(mode.INPUT_SIZE))
    for i in range(len(preprocessed_df), len(df)):
        if i % mode.SAVE == 0 and i != len(preprocessed_df):  # saving periodically because the process is rather long
            print(currentFile, len(df)-i)
            data = data.astype(int)
            data.to_csv(currentFile, mode='a', header=False, index=False)
            data = pd.DataFrame(columns=range(mode.INPUT_SIZE))

        # data: win + champions status + patch
        row = df.iloc[i]
        row_data = list()
        row_data.extend([1 if row[mode.CHAMPIONS_LABEL[k]] == s else 0 for s in mode.CHAMPIONS_STATUS for k in range(mode.CHAMPIONS_SIZE)])
        if mode.image:
            for k in range(mode.PATCHES_SIZE):
                if row['patch'] == mode.PATCHES[k]:
                    row_data.extend([1 for _ in range(mode.CHAMPIONS_SIZE)])
                else:
                    row_data.extend([0 for _ in range(mode.CHAMPIONS_SIZE)])
            if type(mode) != Modes.BR_Mode:
                row_data.extend([row['team'] for _ in range(mode.CHAMPIONS_SIZE)])
        else:
            row_data.extend([1 if row['patch'] == mode.PATCHES[k] else 0 for k in range(mode.PATCHES_SIZE)])
            if type(mode) != Modes.BR_Mode:
                row_data.append(row['team'])
        row_data.append(row['win'])
        data.loc[len(data)] = row_data
    if len(data):
        data = data.astype(int)
        data.to_csv(currentFile, mode='a', header=False, index=False)
    print(currentFile, 'DONE')


def processData(mode):
    if not os.path.isdir(mode.PREPROCESSED_DIR):
        os.makedirs(mode.PREPROCESSED_DIR)

    # listing extracted files and sorting
    extracted_files = [f for f in os.listdir(mode.EXTRACTED_DIR)]
    l = list(map(lambda x: int(x.replace('data_', '').replace('.csv', '')), extracted_files))
    l = sorted(range(len(l)), key=lambda k: l[k])
    extracted_files = [extracted_files[k] for k in l]

    cpu = multiprocessing.cpu_count() - 2
    pool = multiprocessing.Pool(processes=cpu)
    fun = partial(processing, mode)
    pool.map(fun, extracted_files, chunksize=1)
    pool.close()
    pool.join()


def run(mode):
    assert type(mode) in [Modes.ABOTJMCS_Mode, Modes.ABOT_Mode, Modes.BR_Mode], 'Unrecognized mode {}'.format(mode)
    processData(mode)


if __name__ == '__main__':
    run(Modes.BR_Mode())
