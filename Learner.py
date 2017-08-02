#!/usr/bin/env python

# Build and train a neural network to predict the game result
import configparser
import os
import datetime
import random
import time
import sys
import pandas as pd
import tensorflow as tf
import numpy as np

# In order to have compatible models between patches, the input size is oversized
# 7.14: champions 138, patches: 97
# current rythm: 6 champions per season, 24 patches per season
CHAMPIONS_SIZE = 150
PATCHES_SIZE = 150
INPUT_SIZE = CHAMPIONS_SIZE * 8 + PATCHES_SIZE
config = configparser.ConfigParser()
config.read('config.ini')
DATABASE = config['PARAMS']['database']
SHUFFLED_DIR = os.path.join(DATABASE, 'shuffled')
PATCHES = config['PARAMS']['patches'].replace('.', '_').split(',')
PATCHES.extend((PATCHES_SIZE - len(PATCHES)) * [None])
CHAMPIONS_LABEL = config['PARAMS']['sortedChamps'].split(',')
CHAMPIONS_STATUS = ['A', 'B', 'O', 'T', 'J', 'M', 'C', 'S']

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
    def placeholders():
        x = tf.placeholder(tf.float32, shape=[None, INPUT_SIZE])
        y_true = tf.placeholder(tf.float32, shape=[None])
        return x, y_true

    @staticmethod
    def accuracy(y_pred, y_true):
        correct_prediction = tf.equal(tf.sign(y_pred - tf.constant(0.5)), tf.sign(y_true - tf.constant(0.5)))
        accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
        return accuracy

    @staticmethod
    def loss(y_pred, y_true):
        # loss = tf.reduce_mean(tf.squared_difference(y_pred, y_true))
        loss = tf.reduce_mean(-tf.log(tf.constant(1.0) - tf.abs(y_pred - y_true)))
        return loss

    @staticmethod
    def train_op(loss, lr):
        train_op = tf.train.AdamOptimizer(lr).minimize(loss)
        return train_op

    # Architectures
    @staticmethod
    def dense2Arch(x, **kwargs):
        NN = kwargs.pop('NN')
        training = kwargs.pop('training')
        dense1 = tf.layers.dense(x, NN, activation=tf.nn.relu)
        dense2 = tf.layers.dense(dense1, NN, activation=tf.nn.relu)
        dropout = tf.layers.dropout(inputs=dense2, rate=0.5, training=training)
        y_pred = tf.layers.dense(dropout, 1, activation=tf.sigmoid)
        y_pred = tf.reshape(y_pred, [-1])
        return y_pred

    @staticmethod
    def dense3Arch(x, **kwargs):
        NN = kwargs.pop('NN')
        training = kwargs.pop('training')
        dense1 = tf.layers.dense(x, NN, activation=tf.nn.relu)
        dense2 = tf.layers.dense(dense1, NN, activation=tf.nn.relu)
        dense3 = tf.layers.dense(dense2, NN, activation=tf.nn.relu)
        dropout = tf.layers.dropout(inputs=dense3, rate=0.5, training=training)
        y_pred = tf.layers.dense(dropout, 1, activation=tf.sigmoid)
        y_pred = tf.reshape(y_pred, [-1])
        return y_pred

    @staticmethod
    def dense5Arch(x, **kwargs):
        NN = kwargs.pop('NN')
        training = kwargs.pop('training')
        dense1 = tf.layers.dense(x, NN, activation=tf.nn.relu)
        dense2 = tf.layers.dense(dense1, NN, activation=tf.nn.relu)
        dense3 = tf.layers.dense(dense2, NN, activation=tf.nn.relu)
        dense4 = tf.layers.dense(dense3, NN, activation=tf.nn.relu)
        dense5 = tf.layers.dense(dense4, NN, activation=tf.nn.relu)
        dropout = tf.layers.dropout(inputs=dense5, rate=0.5, training=training)
        y_pred = tf.layers.dense(dropout, 1, activation=tf.sigmoid)
        y_pred = tf.reshape(y_pred, [-1])
        return y_pred

    @staticmethod
    def dense12Arch(x, **kwargs):
        NN = kwargs.pop('NN')
        training = kwargs.pop('training')
        denses = [x]
        for k in range(12):
            denses.append(tf.layers.dense(denses[-1], NN, activation=tf.nn.relu))
        dropout = tf.layers.dropout(inputs=denses[-1], rate=0.5, training=training)
        y_pred = tf.layers.dense(dropout, 1, activation=tf.sigmoid)
        y_pred = tf.reshape(y_pred, [-1])
        return y_pred

    @staticmethod
    def dense20Arch(x, **kwargs):
        NN = kwargs.pop('NN')
        training = kwargs.pop('training')
        denses = [x]
        for k in range(20):
            denses.append(tf.layers.dense(denses[-1], NN, activation=tf.nn.relu))
        dropout = tf.layers.dropout(inputs=denses[-1], rate=0.5, training=training)
        y_pred = tf.layers.dense(dropout, 1, activation=tf.sigmoid)
        y_pred = tf.reshape(y_pred, [-1])
        return y_pred


class dataCollector:
    def __init__(self, netType, batchSize):
        self.batchSize = batchSize
        self.i = 0
        self.preprocessed_files = [os.path.join(SHUFFLED_DIR, f) for f in os.listdir(SHUFFLED_DIR)]
        random.shuffle(self.preprocessed_files)
        file = self.preprocessed_files.pop()
        self.df = pd.read_csv(file).sample(frac=1).reset_index(drop=True)
        self.next_batch = {
            'Value': self.nextBatchValue,
        }[netType]

    def nextBatchValue(self):
        batch = [[], []]
        if self.df is None:
            return batch
        j = min(self.i + self.batchSize, len(self.df))
        batch[0] = self.df.iloc[self.i:j, :-1].values.tolist()
        batch[1] = self.df.iloc[self.i:j, -1].values.tolist()  # first column is the value
        if j < len(self.df):
            self.i = j
        else:
            self.i = 0
            if self.preprocessed_files:
                self.df = pd.read_csv(self.preprocessed_files.pop()).sample(frac=1).reset_index(drop=True)
            else:
                self.df = None
        return batch


def learn(netType, netArchi, archi_kwargs, batchSize, checkpoint, report, lr):
    ckpt_dir = os.path.join(DATABASE, 'models', netType + netArchi)

    mappingType = {
        'Value': ValueNetwork,
    }
    if netType not in mappingType:
        raise Exception('Unknown network', netType)
    network = mappingType[netType]

    mappingArchi = {
        'Dense2': network.dense2Arch,
        'Dense3': network.dense3Arch,
        'Dense5': network.dense5Arch,
        'Dense12': network.dense12Arch,
        'Dense20': network.dense20Arch,
    }
    if netArchi not in mappingArchi:
        raise Exception('Unknown netArchi', netArchi)
    architecture = mappingArchi[netArchi]

    with tf.Graph().as_default() as g:
        with tf.Session(graph=g) as sess:
            # Network building
            x, y_true = network.placeholders()
            y_pred = architecture(x, **archi_kwargs)
            acc_ph = network.accuracy(y_pred, y_true)
            loss_ph = network.loss(y_pred, y_true)
            train_op = network.train_op(loss_ph, lr)
            w_acc = []
            w_loss = []

            # Data collector
            collector = dataCollector(netType, batchSize)

            # Restoring last session
            saver = tf.train.Saver(tf.trainable_variables())
            sess.run(tf.global_variables_initializer())
            step = maybe_restore_from_checkpoint(sess, saver, ckpt_dir)
            s = "New session: %s" % ckpt_dir
            with open(os.path.join(ckpt_dir, 'training.log'), 'a+') as f:
                f.write(s + '\n')
            print(s, file=sys.stderr)

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
                feed_dict = {
                    x: batch[0],
                    y_true: batch[1]
                }
                train_start = time.time()
                _, pred_values, real_values, loss, acc = sess.run([train_op, y_pred, y_true, loss_ph, acc_ph], feed_dict=feed_dict)
                train_time = time.time() - train_start
                step_time = time.time() - step_start

                # printing results
                if DEBUG:
                    print(np.array(pred_values[:20]), file=sys.stderr)
                    print(np.array(real_values[:20]), file=sys.stderr)

                # Saving progress
                if step % checkpoint == 0 and step != 0:
                    saver.save(sess, os.path.join(ckpt_dir, "model.ckpt"), global_step=step)
                    print("Checkpoint reached", file=sys.stderr)

                # Logging
                w_acc.append(acc)
                if len(w_acc) > 200:
                    w_acc.pop(0)
                w_loss.append(loss)
                if len(w_loss) > 200:
                    w_loss.pop(0)
                s = "%s: step %d, lr=%.6f, loss = %.4f, acc = %.2f%%, w_loss = %.4f, w_acc = %.2f%% (load=%.3f train=%.3f total=%0.3f sec/step)" % (
                    datetime.datetime.now(), step, lr, loss, 100 * acc, sum(w_loss) / len(w_loss),
                    100 * sum(w_acc) / len(w_acc), batch_time, train_time, step_time)
                with open(os.path.join(ckpt_dir, 'training.log'), 'a+') as f:
                    f.write(s + '\n')
                if step % report == 0:
                    print(s, file=sys.stderr)

            saver.save(sess, os.path.join(ckpt_dir, "model.ckpt"), global_step=step)
            print('Final step saved', file=sys.stderr)
            print('-- End of Session --', file=sys.stderr)


if __name__ == '__main__':
    # Testing (production network will be more sopisticated)
    learn(netType='Value', netArchi='Dense3', archi_kwargs={'NN': 2048, 'training': True}, batchSize=200, checkpoint=1000, report=10, lr=1e-4)
    learn(netType='Value', netArchi='Dense5', archi_kwargs={'NN': 2048, 'training': True}, batchSize=200, checkpoint=1000, report=10, lr=1e-4)
