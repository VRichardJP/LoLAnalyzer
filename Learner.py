# Build and train a neural network to predict the game result

import os
import random
import keras
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
        if keras.backend.learning_phase() == 1:  # training phase
            self.data_files = [os.path.join(mode.TRAINING_DIR, f) for f in os.listdir(mode.TRAINING_DIR)]
        elif keras.backend.learning_phase() == 0:
            self.data_files = [os.path.join(mode.TESTING_DIR, f) for f in os.listdir(mode.TESTING_DIR)]
        else:
            raise Exception('Unknown flag {}'.format(keras.backend.learning_phase()))
        random.shuffle(self.data_files)
        file = self.data_files.pop()
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
                if self.data_files:
                    self.df = pd.read_csv(self.data_files.pop()).sample(frac=1).reset_index(drop=True)
                else:
                    yield x, y  # last batch
                    break
            yield x, y


def training(mode, network, restore, window_size=1000):
    keras.backend.set_learning_phase(1)  # training phase

    model_file = os.path.join(mode.CKPT_DIR, str(network) + '.h5')
    print('-- New training Session --', file=sys.stderr)
    print(model_file, file=sys.stderr)

    network.build()
    if os.path.isfile(model_file) and restore:
        print('Restoring previous session', file=sys.stderr)
        network.model = keras.models.load_model(model_file)
    else:
        print('Training a new model', file=sys.stderr)

    collector = dataCollector(mode, network.batch_size)

    step = 0
    windowed_loss = []
    windowed_acc = []
    for x, y in collector.batchGenerator():
        step += 1
        res = network.model.train_on_batch(x, y)

        windowed_loss.append(res[0])
        if len(windowed_loss) > window_size:
            windowed_loss.pop(0)
        windowed_acc.append(res[1])
        if len(windowed_acc) > window_size:
            windowed_acc.pop(0)

        if step % network.report == 0:
            mean_loss = sum(windowed_loss) / len(windowed_loss)
            mean_acc = sum(windowed_acc) / len(windowed_acc)

            print('step {}, loss={:.4f}, acc={:.4f}, w_loss={:.4f}, w_acc={:.4f}'.format(step, res[0], res[1], mean_loss, mean_acc), file=sys.stderr)

    print('Saving model to {}'.format(model_file), file=sys.stderr)
    if not os.path.isdir(mode.CKPT_DIR):
        os.makedirs(mode.CKPT_DIR)
    network.model.save(model_file)
    print('-- End of training Session --', file=sys.stderr)


def testing(mode, network):
    keras.backend.set_learning_phase(0)  # testing phase

    model_file = os.path.join(mode.CKPT_DIR, str(network) + '.h5')
    print('-- New evaluating Session --', file=sys.stderr)
    print(model_file, file=sys.stderr)

    if not os.path.isfile(model_file):
        print('Cannot find {}'.format(model_file), file=sys.stderr)
        return
    network.model = keras.models.load_model(model_file)
    collector = dataCollector(mode, network.batch_size)

    step = 0
    acc = []
    for x, y in collector.batchGenerator():
        step += 1
        res = network.model.evaluate(x, y, verbose=0)
        acc.append(res[1])
        if step % network.report == 0:
            mean_acc = sum(acc) / len(acc)
            print('step {}, acc={:.4f}, overall_acc={:.4f}'.format(step, res[1], mean_acc), file=sys.stderr)
    print('-- End of evaluating Session --', file=sys.stderr)


def run(mode, network, restore):
    assert isinstance(network, Networks.BaseModel), 'Unrecognized network {}'.format(network)

    training(mode, network, restore)
    testing(mode, network)


if __name__ == '__main__':
    m = Modes.ABR_TJMCS_Mode(['7.16', '7.17'])
    n = Networks.DenseUniform(mode=m, n_hidden_layers=5, NN=1024, dropout=0.2, batch_size=1000, report=1)
    run(m, n, True)
