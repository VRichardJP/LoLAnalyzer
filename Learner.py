# Build and train a neural network to predict the game result

import os
import random
import Modes
import Networks
import sys
import pandas as pd
import numpy as np

np.set_printoptions(formatter={'float_kind': lambda x: "%.2f" % x}, linewidth=200)


class dataCollector:
    def __init__(self, mode, batchSize):
        self.batchSize = batchSize
        self.i = 0
        self.preprocessed_files = [os.path.join(mode.SHUFFLED_DIR, f) for f in os.listdir(mode.SHUFFLED_DIR)]
        random.shuffle(self.preprocessed_files)
        file = self.preprocessed_files.pop()
        self.df = pd.read_csv(file).sample(frac=1).reset_index(drop=True)

    def batchGenerator(self):
        while True:
            j = min(self.i + self.batchSize, len(self.df))
            x = self.df.iloc[self.i:j, :-1].values.tolist()
            y = self.df.iloc[self.i:j, -1:].values.tolist()  # last column is the win value
            if j < len(self.df):
                self.i = j
            else:
                self.i = 0
                if self.preprocessed_files:
                    self.df = pd.read_csv(self.preprocessed_files.pop()).sample(frac=1).reset_index(drop=True)
                else:
                    break
            yield x, y


def train(mode, network):
    ckpt_dir = os.path.join(mode.DATABASE, 'models', network)
    print('-- New training Session --', file=sys.stderr)
    print(ckpt_dir, file=sys.stderr)

    network.build()
    collector = dataCollector(mode, network.batch_size)

    step = 0
    for x, y in collector.batchGenerator():
        print('step {}'.format(step))
        network.model.train_on_batch(x, y)

    print('-- End of training Session --', file=sys.stderr)


def evaluate(mode, network):
    ckpt_dir = os.path.join(mode.DATABASE, 'models', network)
    print('-- New evaluating Session --', file=sys.stderr)
    print(ckpt_dir, file=sys.stderr)

    network.build()
    collector = dataCollector(mode, network.batch_size)

    step = 0
    for x, y in collector.batchGenerator():
        print('step {}'.format(step))
        scores = network.model.evaluate(x, y)
        print("\n%s: %.2f%%" % (network.model.metrics_names[1], scores[1] * 100))

    print('-- End of evaluating Session --', file=sys.stderr)


def run(mode, network):
    assert type(mode) in [Modes.ABOTJMCS_Mode, Modes.ABOT_Mode, Modes.BR_Mode], 'Unrecognized mode {}'.format(mode)
    assert isinstance(network, Networks.BaseModel), 'Unrecognized network {}'.format(network)

    train(mode, network)


if __name__ == '__main__':
    m = Modes.BR_Mode()
    run(m, Networks.DenseUniform(m, 5, 256))
