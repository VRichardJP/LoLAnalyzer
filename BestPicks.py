import configparser
import os
import sys
from PyQt5.QtWidgets import *
import pandas as pd
import tensorflow as tf

from Learner import ValueNetwork, maybe_restore_from_checkpoint

CHAMPIONS_SIZE = 150
PATCHES_SIZE = 150

config = configparser.ConfigParser()
config.read('config.ini')
DATABASE = config['PARAMS']['database']
CHAMPIONS = ['...']
CHAMPIONS.extend(sorted(config['PARAMS']['sortedChamps'].split(',')))
ROLES = ['...', 'Top', 'Jungle', 'Mid', 'Carry', 'Support']
PATCHES = config['PARAMS']['patches'].replace('.', '_').split(',')
CHAMPIONS_LABEL = config['PARAMS']['sortedChamps'].split(',')
CHAMPIONS_STATUS = ['A', 'B', 'O', 'T', 'J', 'M', 'C', 'S']
PATCH = PATCHES_SIZE * [0]
PATCH[len(PATCHES) - 1] = 1  # current patch

netArchi = 'Dense3'
archi_kwargs={'NN': 2048}


class App(QDialog):
    def __init__(self):
        super().__init__()
        self.title = 'LoLAnalyzer'
        self.left = 10
        self.top = 10
        self.width = 660
        self.height = 400
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Main Layout
        mainBoxLayout = QGridLayout()
        self.setLayout(mainBoxLayout)

        # Bans Layout
        bansGB = QGroupBox('Bans')
        BansLayout = QGridLayout()
        self.player1Ban = QComboBox()
        self.player1Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player1Ban, 0, 0)
        self.player2Ban = QComboBox()
        self.player2Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player2Ban, 0, 1)
        self.player3Ban = QComboBox()
        self.player3Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player3Ban, 0, 2)
        self.player4Ban = QComboBox()
        self.player4Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player4Ban, 0, 3)
        self.player5Ban = QComboBox()
        self.player5Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player5Ban, 0, 4)
        self.player6Ban = QComboBox()
        self.player6Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player6Ban, 1, 0)
        self.player7Ban = QComboBox()
        self.player7Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player7Ban, 1, 1)
        self.player8Ban = QComboBox()
        self.player8Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player8Ban, 1, 2)
        self.player9Ban = QComboBox()
        self.player9Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player9Ban, 1, 3)
        self.player10Ban = QComboBox()
        self.player10Ban.addItems(CHAMPIONS)
        BansLayout.addWidget(self.player10Ban, 1, 4)
        bansGB.setLayout(BansLayout)
        mainBoxLayout.addWidget(bansGB, 0, 0, 1, 3)

        # Your team picks Layout
        yourTeamGB = QGroupBox('Your Team')
        yourTeamLayout = QGridLayout()
        self.player1Pick = QComboBox()
        self.player1Pick.addItems(CHAMPIONS)
        yourTeamLayout.addWidget(self.player1Pick, 0, 0)
        self.player1Role = QComboBox()
        self.player1Role.addItems(ROLES)
        yourTeamLayout.addWidget(self.player1Role, 0, 1)
        self.player2Pick = QComboBox()
        self.player2Pick.addItems(CHAMPIONS)
        yourTeamLayout.addWidget(self.player2Pick, 1, 0)
        self.player2Pick = QComboBox()
        self.player2Pick.addItems(ROLES)
        yourTeamLayout.addWidget(self.player2Pick, 1, 1)
        self.player3Pick = QComboBox()
        self.player3Pick.addItems(CHAMPIONS)
        yourTeamLayout.addWidget(self.player3Pick, 2, 0)
        self.player3Pick = QComboBox()
        self.player3Pick.addItems(ROLES)
        yourTeamLayout.addWidget(self.player3Pick, 2, 1)
        self.player4Pick = QComboBox()
        self.player4Pick.addItems(CHAMPIONS)
        yourTeamLayout.addWidget(self.player4Pick, 3, 0)
        self.player4Pick = QComboBox()
        self.player4Pick.addItems(ROLES)
        yourTeamLayout.addWidget(self.player4Pick, 3, 1)
        self.player5Pick = QComboBox()
        self.player5Pick.addItems(CHAMPIONS)
        yourTeamLayout.addWidget(self.player5Pick, 4, 0)
        self.player5Pick = QComboBox()
        self.player5Pick.addItems(ROLES)
        yourTeamLayout.addWidget(self.player5Pick, 4, 1)
        yourTeamGB.setLayout(yourTeamLayout)
        mainBoxLayout.addWidget(yourTeamGB, 1, 0)

        # Ennemy team picks Layout
        ennemyTeamGB = QGroupBox('Ennemy Team')
        ennemyTeamLayout = QVBoxLayout()
        self.player6Pick = QComboBox()
        self.player6Pick.addItems(CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player6Pick)
        self.player7Pick = QComboBox()
        self.player7Pick.addItems(CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player7Pick)
        self.player8Pick = QComboBox()
        self.player8Pick.addItems(CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player8Pick)
        self.player9Pick = QComboBox()
        self.player9Pick.addItems(CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player9Pick)
        self.player10Pick = QComboBox()
        self.player10Pick.addItems(CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player10Pick)
        ennemyTeamGB.setLayout(ennemyTeamLayout)
        mainBoxLayout.addWidget(ennemyTeamGB, 1, 2)

        # Best picks Layout
        bestPicksGB = QGroupBox('Best Picks')
        bestPicksLayout = QGridLayout()
        yourRoleLabel = QLabel()
        yourRoleLabel.setText('Your role:')
        bestPicksLayout.addWidget(yourRoleLabel, 0, 0)
        self.yourRole = QComboBox()
        self.yourRole.addItems(ROLES)
        bestPicksLayout.addWidget(self.yourRole, 0, 1)
        self.generateButton = QPushButton('Analyze')
        self.generateButton.clicked.connect(lambda: self.generate())
        bestPicksLayout.addWidget(self.generateButton, 0, 2)
        self.results = QTableWidget()
        self.results.setRowCount(4)
        self.results.setColumnCount(2)
        self.results.horizontalHeader().hide()
        self.results.verticalHeader().hide()
        # self.results.setItem(0, 0, QTableWidgetItem("Item (1,1)"))
        # self.results.setItem(0, 1, QTableWidgetItem("Item (1,2)"))
        # self.results.setItem(1, 0, QTableWidgetItem("Item (2,1)"))
        # self.results.setItem(1, 1, QTableWidgetItem("Item (2,2)"))
        # self.results.setItem(2, 0, QTableWidgetItem("Item (3,1)"))
        # self.results.setItem(2, 1, QTableWidgetItem("Item (3,2)"))
        # self.results.setItem(3, 0, QTableWidgetItem("Item (4,1)"))
        # self.results.setItem(3, 1, QTableWidgetItem("Item (4,2)"))

        bestPicksLayout.addWidget(self.results, 1, 0, 1, 3)

        bestPicksGB.setLayout(bestPicksLayout)
        mainBoxLayout.addWidget(bestPicksGB, 1, 1)

        # Centering window
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self.show()

        network = ValueNetwork
        netType = 'Value'

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


        # Building the neural network
        with tf.Graph().as_default() as g:
            with tf.Session(graph=g) as self.sess:
                # Network building
                self.x, y_true = network.placeholders()
                self.y_pred = architecture(self.x, **archi_kwargs)
                # acc_ph = network.accuracy(y_pred, y_true)
                # loss_ph = network.loss(y_pred, y_true)
                # train_op = network.train_op(loss_ph, lr)
                w_acc = []
                w_loss = []

                # Restoring last session
                saver = tf.train.Saver(tf.trainable_variables())
                self.sess.run(tf.global_variables_initializer())
                ckpt_dir = os.path.join(DATABASE, 'models', netType + netArchi)
                step = maybe_restore_from_checkpoint(self.sess, saver, ckpt_dir)
                s = "New session: %s" % ckpt_dir
                with open(os.path.join(ckpt_dir, 'testing.log'), 'a+') as f:
                    f.write(s + '\n')
                print(s)

    def generate(self):
        currentState = {champ: 'A' for champ in CHAMPIONS[1:]}
        bans = [self.player1Ban, self.player2Ban, self.player3Ban, self.player4Ban, self.player5Ban, self.player6Ban, self.player7Ban,
                self.player8Ban, self.player9Ban, self.player10Ban]
        picks = [(self.player1Pick, self.player1Role), (self.player2Pick, self.player2Role), (self.player3Pick, self.player3Role),
                 (self.player4Pick, self.player4Role), (self.player5Pick, self.player5Role), (self.player6Pick, 'Opp'), (self.player7Pick, 'Opp'),
                 (self.player8Pick, 'Opp'), (self.player9Pick, 'Opp'), (self.player10Pick, 'Opp')]
        for ban in bans:
            currentState[ban] = 'B'
        for (pick, role) in picks:
            if role[0] not in CHAMPIONS_STATUS:
                raise Exception
            currentState[pick] = role[0]

        yourRole = self.yourRole[0]
        if yourRole not in CHAMPIONS_STATUS:
            raise Exception

        possibleStates = []
        for champ in CHAMPIONS[1:]:
            if currentState[champ] != 'A':
                continue
            state = dict(currentState)
            state[champ] = yourRole
            possibleStates.append(state)

        data = pd.DataFrame()

        for row in possibleStates:
            row_data = list()
            row_data.extend([1 if row[champ] == s else 0 for s in CHAMPIONS_STATUS for champ in CHAMPIONS_LABEL])
            row_data.extend([0 for s in CHAMPIONS_STATUS for k in range(CHAMPIONS_SIZE - len(CHAMPIONS_LABEL))])
            row_data.extend([1 if row['patch'] == PATCHES[k] else 0 for k in range(PATCHES_SIZE)])
            data = data.append([row_data])

        batch = [[], []]
        batch[0] = self.data

        feed_dict = {
            self.x: batch[0],
        }
        pred_values = self.sess.run([self.y_pred], feed_dict=feed_dict)
        possibleStates = [x for (y,x) in sorted(zip(pred_values, possibleStates))]
        print(possibleStates)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
