#!/usr/bin/env python

# Build and train a neural network to predict the game result
import configparser
import multiprocessing
import os
import datetime
import queue
import time
import sys
import pandas as pd
import tensorflow as tf
import numpy as np
from multiprocessing import Manager

np.set_printoptions(formatter={'float_kind': lambda x: "%.2f" % x}, linewidth=200)
DEBUG = False


def maybe_restore_from_checkpoint(sess, saver, ckpt_dir):
    print("Trying to restore from checkpoint in dir", ckpt_dir, file=sys.stderr)
    if not os.path.exists(ckpt_dir):
        os.makedirs(ckpt_dir)
    ckpt = tf.train.get_checkpoint_state(ckpt_dir)
    if ckpt and ckpt.model_checkpoint_path:
        print("Checkpoint file is ", ckpt.model_checkpoint_path, file=sys.stderr)
        saver.restore(sess, ckpt.model_checkpoint_path)
        global_step = int(ckpt.model_checkpoint_path.split('/')[-1].split('-')[-1])
        print("Restored from checkpoint %s" % global_step, file=sys.stderr)
        return global_step
    else:
        print("No checkpoint file found", file=sys.stderr)
        return 0


class ValueNetwork:
    @staticmethod
    def placeholders(X, Y):
        x = tf.placeholder(tf.float32, shape=[None, X, Y])
        y_true = tf.placeholder(tf.float32, shape=[None])
        return x, y_true

    @staticmethod
    def accuracy(y_pred, y_true):
        correct_prediction = tf.equal(tf.sign(y_pred - tf.constant(0.5)), tf.sign(y_true - tf.constant(0.5)))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        return accuracy

    @staticmethod
    def loss(y_pred, y_true):
        loss = tf.reduce_mean(tf.squared_difference(y_pred, y_true))
        return loss

    @staticmethod
    def train_op(loss, lr):
        train_op = tf.train.AdamOptimizer(lr).minimize(loss)
        return train_op

    # Architectures
    @staticmethod
    def dense2Arch(x, X, Y, **kwargs):
        NN = kwargs.pop('NN')
        x_flat = tf.reshape(x, [-1, X * Y])
        dense1 = tf.layers.dense(x_flat, NN, activation=tf.nn.relu)
        dense2 = tf.layers.dense(dense1, NN // 2, activation=tf.nn.relu)
        y_pred = tf.layers.dense(dense2, 1, activation=tf.sigmoid)
        y_pred = tf.reshape(y_pred, [-1])
        return y_pred

    @staticmethod
    def dense3Arch(x, X, Y, **kwargs):
        NN = kwargs.pop('NN')
        x_flat = tf.reshape(x, [-1, X * Y])
        dense1 = tf.layers.dense(x_flat, NN, activation=tf.nn.relu)
        dense2 = tf.layers.dense(dense1, NN // 2, activation=tf.nn.relu)
        dense3 = tf.layers.dense(dense2, NN // 4, activation=tf.nn.relu)
        y_pred = tf.layers.dense(dense3, 1, activation=tf.sigmoid)
        y_pred = tf.reshape(y_pred, [-1])
        return y_pred

class dataCollector:
    def __init__(self, dataFile, config, netType, batchSize):
        if netType == 'Value':
            CHAMPIONS_LABEL = list(config['CHAMPIONS'])
            CHAMPION_STATUS = ['A', 'B', 'O', 'T', 'J', 'M', 'C', 'S']
            names = CHAMPIONS_LABEL[:]
            names.append('blue_win')
            df = pd.read_csv(dataFile, names=names, skiprows=1).sample(frac=1).reset_index(drop=True)

            # Multi-processing to collect the data faster
            manager = Manager()
            self.q_batch = manager.Queue(1)
            n_proc = 1 if DEBUG else multiprocessing.cpu_count()
            self.miniCollectors = []
            samples = np.array_split(df, n_proc)
            for sample in samples:
                sample = sample.reset_index(drop=True)
                if DEBUG:
                    print(sample, file=sys.stderr)
                self.miniCollectors.append(multiprocessing.Process(target=dataCollector.miniCollectorValue, args=(sample, batchSize, self.q_batch, CHAMPIONS_LABEL, CHAMPION_STATUS)))
                self.miniCollectors[-1].start()
        else:
            raise Exception('unknown netType', netType)

    def next_batch(self):
        while True:
            self.miniCollectors = [mc for mc in self.miniCollectors if mc.is_alive()]
            if not self.miniCollectors:
                print('No collector left', file=sys.stderr)
                return None
            try:
                return self.q_batch.get(timeout=60)
            except queue.Empty:
                continue

    @staticmethod
    def miniCollectorValue(df, batchSize, q_batch, CHAMPIONS_LABEL, CHAMPION_STATUS):
        print(os.getpid(), 'miniCollectorValue starting', file=sys.stderr)
        end = df.shape[0]
        i = 0
        while True:
            if i >= end:
                break
            j = i + batchSize
            batch = [[], []]
            batch[0] = [[[1 if row[champ] == s else 0 for s in CHAMPION_STATUS] for champ in CHAMPIONS_LABEL] for _, row in
                        df.iloc[i:min(j, end)].iterrows()]
            batch[1] = [v for v in df.iloc[i: min(j, end), df.columns.get_loc('blue_win')]]
            q_batch.put(batch)
            i = j
        print(os.getpid(), 'miniCollectorValue end', file=sys.stderr)


def learn(netType, netArchi, archi_kwargs, batchSize, checkpoint, lr):
    ckpt_dir = os.path.join(DATABASE, 'models', PATCH, netType + netArchi)
    dataFile = os.path.join(DATABASE, PATCH, 'data.csv')

    # Network config
    mapType = {
        'Value': ValueNetwork,
        }
    if netType == 'Value':
        network = ValueNetwork

    else:
        raise Exception('Unknown netType', netType)
    if netArchi == 'Dense2':
        architecture = network.dense2Arch
    elif netArchi == 'Dense3':
        architecture = network.dense3Arch
    else:
        raise Exception('Unknown netArchi', netArchi)

    with tf.Graph().as_default() as g:
        with tf.Session() as sess:
            # Network building
            x, y_true = network.placeholders(X, Y)
            y_pred = architecture(x, X, Y, **archi_kwargs)
            acc_ph = network.accuracy(y_pred, y_true)
            loss_ph = network.loss(y_pred, y_true)
            train_op = network.train_op(loss_ph, lr)
            w_acc = []
            w_loss = []

            # Data collector
            collector = dataCollector(dataFile, config, netType, batchSize)

            # Restoring last session
            saver = tf.train.Saver(tf.trainable_variables())
            sess.run(tf.global_variables_initializer())
            step = maybe_restore_from_checkpoint(sess, saver, ckpt_dir)
            s = "New session: %s" % ckpt_dir
            with open(os.path.join(ckpt_dir, 'training.log'), 'a+') as f:
                f.write(s + '\n')
            print(s)

            while True:
                step_start = time.time()

                # Getting batch
                batch_start = time.time()
                batch = collector.next_batch()
                if not batch or batch == [[], []]:
                    break
                batch_time = time.time() - batch_start

                # Training
                step += 1
                feed_dict = {}
                feed_dict[x] = batch[0]
                feed_dict[y_true] = batch[1]
                train_start = time.time()
                _, pred_values, real_values, loss, acc = sess.run([train_op, y_pred, y_true, loss_ph, acc_ph], feed_dict=feed_dict)
                train_time = time.time() - train_start
                step_time = time.time() - step_start

                # printing results
                if DEBUG:
                    print(np.array(pred_values[:20]))
                    print(np.array(real_values[:20]))

                # Saving progress
                if step % checkpoint == 0 and step != 0:
                    saver.save(sess, os.path.join(ckpt_dir, "model.ckpt"), global_step=step)
                    print("Checkpoint reached", file=sys.stderr)

                # Logging
                w_acc.append(acc)
                if len(w_acc) > 100:
                    w_acc.pop(0)
                w_loss.append(loss)
                if len(w_loss) > 100:
                    w_loss.pop(0)
                s = "%s: step %d, lr=%.6f, loss = %.4f, acc = %.2f%%, w_loss = %.4f, w_acc = %.2f%% (load=%.3f train=%.3f total=%0.3f sec/step)" % (
                    datetime.datetime.now(), step, lr, loss, 100 * acc, sum(w_loss) / len(w_loss),
                    100 * sum(w_acc) / len(w_acc), batch_time, train_time, step_time)
                with open(os.path.join(ckpt_dir, 'training.log'), 'a+') as f:
                    f.write(s + '\n')
                print(s)

            saver.save(sess, os.path.join(ckpt_dir, "model.ckpt"), global_step=step)
            print('Final step saved', file=sys.stderr)
            print('-- End of Session --', file=sys.stderr)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('config.ini')
    DATABASE = config['CONFIG']['database']
    PATCH = config['CONFIG']['patch']
    CHAMPIONS_LABEL = list(config['CHAMPIONS'])
    CHAMPION_STATUS = ['A', 'B', 'O', 'T', 'J', 'M', 'C', 'S']
    Y = len(CHAMPION_STATUS)

    X = len(CHAMPIONS_LABEL)
    Nfeat = 8  # Nb of feature per champ (average)
    learn(netType='Value', netArchi='Dense3', archi_kwargs={'NN': X*Nfeat}, batchSize=200, checkpoint=100, lr=1e-4)
