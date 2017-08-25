# Evaluate the best pick for the given role and team

import os
import sys
import numpy as np
from PyQt5.QtWidgets import *
from collections import OrderedDict

import Modes
import Networks

sys._excepthook = sys.excepthook


class UnrecognizedMode(Exception):
    pass


def my_exception_hook(exctype, value, traceback):
    # Print the error and traceback
    print(exctype, value, traceback)
    # Call the normal Exception hook after
    # noinspection PyProtectedMember
    sys._excepthook(exctype, value, traceback)
    sys.exit(1)


# Set the exception hook to our wrapping function
sys.excepthook = my_exception_hook


class App(QDialog):
    # noinspection PyArgumentList,PyUnresolvedReferences
    def __init__(self, mode, network):
        super().__init__()
        self.title = 'LoLAnalyzer'
        self.left = 10
        self.top = 10
        self.width = 700
        self.height = 600
        self.mode = mode
        self.network = network
        self.yourTeam = None
        self.yourRole = None
        self.pick_order = None
        self.role_order = None

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        # Main Layout
        mainBoxLayout = QGridLayout()
        self.setLayout(mainBoxLayout)

        # Bans Layout
        bansGB = QGroupBox('Bans')
        BansLayout = QGridLayout()
        self.player1Ban = QComboBox()
        self.player1Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player1Ban, 0, 0)
        self.player2Ban = QComboBox()
        self.player2Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player2Ban, 0, 1)
        self.player3Ban = QComboBox()
        self.player3Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player3Ban, 0, 2)
        self.player4Ban = QComboBox()
        self.player4Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player4Ban, 0, 3)
        self.player5Ban = QComboBox()
        self.player5Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player5Ban, 0, 4)
        self.player6Ban = QComboBox()
        self.player6Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player6Ban, 1, 0)
        self.player7Ban = QComboBox()
        self.player7Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player7Ban, 1, 1)
        self.player8Ban = QComboBox()
        self.player8Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player8Ban, 1, 2)
        self.player9Ban = QComboBox()
        self.player9Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player9Ban, 1, 3)
        self.player10Ban = QComboBox()
        self.player10Ban.addItems(self.mode.BP_CHAMPIONS)
        BansLayout.addWidget(self.player10Ban, 1, 4)
        bansGB.setLayout(BansLayout)
        mainBoxLayout.addWidget(bansGB, 0, 0, 1, 3)

        # Your team picks Layout
        yourTeamGB = QGroupBox('Your Team')
        yourTeamLayout = QGridLayout()
        self.player1Pick = QComboBox()
        self.player1Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player1Pick.currentTextChanged.connect(self.pick)
        yourTeamLayout.addWidget(self.player1Pick, 0, 0)
        self.player1Role = QComboBox()
        self.player1Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player1Role, 0, 1)
        self.player2Pick = QComboBox()
        self.player2Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player2Pick.currentTextChanged.connect(self.pick)
        yourTeamLayout.addWidget(self.player2Pick, 1, 0)
        self.player2Role = QComboBox()
        self.player2Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player2Role, 1, 1)
        self.player3Pick = QComboBox()
        self.player3Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player3Pick.currentTextChanged.connect(self.pick)
        yourTeamLayout.addWidget(self.player3Pick, 2, 0)
        self.player3Role = QComboBox()
        self.player3Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player3Role, 2, 1)
        self.player4Pick = QComboBox()
        self.player4Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player4Pick.currentTextChanged.connect(self.pick)
        yourTeamLayout.addWidget(self.player4Pick, 3, 0)
        self.player4Role = QComboBox()
        self.player4Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player4Role, 3, 1)
        self.player5Pick = QComboBox()
        self.player5Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player5Pick.currentTextChanged.connect(self.pick)
        yourTeamLayout.addWidget(self.player5Pick, 4, 0)
        self.player5Role = QComboBox()
        self.player5Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player5Role, 4, 1)
        yourTeamGB.setLayout(yourTeamLayout)
        mainBoxLayout.addWidget(yourTeamGB, 1, 0)

        # Enemy team picks Layout
        enemyTeamGB = QGroupBox('Enemy Team')
        enemyTeamLayout = QGridLayout()
        self.player6Pick = QComboBox()
        self.player6Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player6Pick.currentTextChanged.connect(self.pick)
        enemyTeamLayout.addWidget(self.player6Pick, 0, 0)
        self.player6Role = QComboBox()
        self.player6Role.addItems(self.mode.BP_ROLES)
        enemyTeamLayout.addWidget(self.player6Role, 0, 1)
        self.player7Pick = QComboBox()
        self.player7Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player7Pick.currentTextChanged.connect(self.pick)
        enemyTeamLayout.addWidget(self.player7Pick, 1, 0)
        self.player7Role = QComboBox()
        self.player7Role.addItems(self.mode.BP_ROLES)
        enemyTeamLayout.addWidget(self.player7Role, 1, 1)
        self.player8Pick = QComboBox()
        self.player8Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player8Pick.currentTextChanged.connect(self.pick)
        enemyTeamLayout.addWidget(self.player8Pick, 2, 0)
        self.player8Role = QComboBox()
        self.player8Role.addItems(self.mode.BP_ROLES)
        enemyTeamLayout.addWidget(self.player8Role, 2, 1)
        self.player9Pick = QComboBox()
        self.player9Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player9Pick.currentTextChanged.connect(self.pick)
        enemyTeamLayout.addWidget(self.player9Pick, 3, 0)
        self.player9Role = QComboBox()
        self.player9Role.addItems(self.mode.BP_ROLES)
        enemyTeamLayout.addWidget(self.player9Role, 3, 1)
        self.player10Pick = QComboBox()
        self.player10Pick.addItems(self.mode.BP_CHAMPIONS)
        self.player10Pick.currentTextChanged.connect(self.pick)
        enemyTeamLayout.addWidget(self.player10Pick, 4, 0)
        self.player10Role = QComboBox()
        self.player10Role.addItems(self.mode.BP_ROLES)
        enemyTeamLayout.addWidget(self.player10Role, 4, 1)
        enemyTeamGB.setLayout(enemyTeamLayout)
        mainBoxLayout.addWidget(enemyTeamGB, 1, 2)

        # Best picks Layout
        bestPicksGB = QGroupBox('Best Picks')
        bestPicksLayout = QGridLayout()
        yourTeamButtonGroup = QButtonGroup()
        blueTeamButton = QRadioButton('Blue Team')
        redTeamButton = QRadioButton('Red Team')
        blueTeamButton.setChecked(True)
        yourTeamButtonGroup.addButton(blueTeamButton)
        yourTeamButtonGroup.addButton(redTeamButton)
        yourTeamButtonGroup.buttonClicked['QAbstractButton *'].connect(self.teamChoice)
        bestPicksLayout.addWidget(blueTeamButton, 0, 0)
        bestPicksLayout.addWidget(redTeamButton, 1, 0)
        self.evaluateButton = QPushButton('Wait...')
        self.evaluateButton.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self.evaluateButton.clicked.connect(lambda: self.evaluate())
        bestPicksLayout.addWidget(self.evaluateButton, 0, 1)
        self.generateButton = QPushButton('Wait...')
        self.generateButton.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self.generateButton.clicked.connect(lambda: self.generate())
        bestPicksLayout.addWidget(self.generateButton, 1, 1)

        self.results = QTableWidget()
        # self.results.setRowCount(4)
        self.results.setColumnCount(2)
        self.results.horizontalHeader().hide()
        self.results.verticalHeader().hide()
        bestPicksLayout.addWidget(self.results, 2, 0, 1, 2)

        bestPicksGB.setLayout(bestPicksLayout)
        mainBoxLayout.addWidget(bestPicksGB, 1, 1)

        # Centering window
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self.show()

        self.teamChoice(blueTeamButton)
        self.buildNetwork()

    def teamChoice(self, button):
        self.yourTeam = button.text()[0]

        self.player1Pick.setEnabled(False)
        self.player1Pick.setCurrentIndex(0)
        self.player1Role.setEnabled(True)
        self.player1Role.setCurrentIndex(0)
        self.player2Pick.setEnabled(False)
        self.player2Pick.setCurrentIndex(0)
        self.player2Role.setEnabled(True)
        self.player2Role.setCurrentIndex(0)
        self.player3Pick.setEnabled(False)
        self.player3Pick.setCurrentIndex(0)
        self.player3Role.setEnabled(True)
        self.player3Role.setCurrentIndex(0)
        self.player4Pick.setEnabled(False)
        self.player4Pick.setCurrentIndex(0)
        self.player4Role.setEnabled(True)
        self.player4Role.setCurrentIndex(0)
        self.player5Pick.setEnabled(False)
        self.player5Pick.setCurrentIndex(0)
        self.player5Role.setEnabled(True)
        self.player5Role.setCurrentIndex(0)
        self.player6Pick.setEnabled(False)
        self.player6Pick.setCurrentIndex(0)
        self.player6Role.setEnabled(True)
        self.player6Role.setCurrentIndex(0)
        self.player7Pick.setEnabled(False)
        self.player7Pick.setCurrentIndex(0)
        self.player7Role.setEnabled(True)
        self.player7Role.setCurrentIndex(0)
        self.player8Pick.setEnabled(False)
        self.player8Pick.setCurrentIndex(0)
        self.player8Role.setEnabled(True)
        self.player8Role.setCurrentIndex(0)
        self.player9Pick.setEnabled(False)
        self.player9Pick.setCurrentIndex(0)
        self.player9Role.setEnabled(True)
        self.player9Role.setCurrentIndex(0)
        self.player10Pick.setEnabled(False)
        self.player10Pick.setCurrentIndex(0)
        self.player10Role.setEnabled(True)
        self.player10Role.setCurrentIndex(0)

        if self.yourTeam == 'B':
            self.player1Pick.setEnabled(True)
            self.generateButton.setEnabled(True)
            self.pick_order = [self.player1Pick, self.player6Pick, self.player7Pick, self.player2Pick, self.player3Pick, self.player8Pick,
                               self.player9Pick, self.player4Pick, self.player5Pick, self.player10Pick]
            self.role_order = [self.player1Role, self.player6Role, self.player7Role, self.player2Role, self.player3Role, self.player8Role,
                               self.player9Role, self.player4Role, self.player5Role, self.player10Role]
        else:
            self.player6Pick.setEnabled(True)
            self.generateButton.setEnabled(False)
            self.pick_order = [self.player6Pick, self.player1Pick, self.player2Pick, self.player7Pick, self.player8Pick, self.player3Pick,
                               self.player4Pick, self.player9Pick, self.player10Pick, self.player5Pick]
            self.role_order = [self.player6Role, self.player1Role, self.player2Role, self.player7Role, self.player8Role, self.player3Role,
                               self.player4Role, self.player9Role, self.player10Role, self.player5Role]

    def pick(self):
        i = self.pick_order.index(self.sender())
        if self.sender().currentIndex() != 0:
            if i + 1 < len(self.pick_order):
                self.pick_order[i + 1].setEnabled(True)
        else:
            for j in range(i + 1, len(self.pick_order)):
                self.pick_order[i + 1].setCurrentIndex(0)
                self.pick_order[i + 1].setEnabled(False)
                self.role_order[i + 1].setCurrentIndex(0)

        # get the last available combobox, if in player 1-5 then we set self.yourRole, else disable generation
        l = [playerPick.isEnabled() for playerPick in self.pick_order]
        currentPickIndex = -1 if False not in l else l.index(False) - 1
        if currentPickIndex >= 0 and self.pick_order[currentPickIndex] in [self.player1Pick, self.player2Pick, self.player3Pick, self.player4Pick,
                                                                           self.player5Pick]:
            self.generateButton.setEnabled(True)
            self.yourRole = self.role_order[currentPickIndex]
        else:
            self.generateButton.setEnabled(False)
            self.yourRole = None

    def buildNetwork(self):
        import keras
        keras.backend.set_learning_phase(0)  # evaluation = testing phase

        model_file = os.path.join(self.mode.CKPT_DIR, str(self.network) + '.h5')
        print('-- New evaluating Session --', file=sys.stderr)
        print(model_file, file=sys.stderr)

        if not os.path.isfile(model_file):
            print('Cannot find {}'.format(model_file), file=sys.stderr)
            return
        self.network.model = keras.models.load_model(model_file)

        self.generateButton.setText('Analyze')
        self.generateButton.setEnabled(True)
        self.evaluateButton.setText('Evaluate')
        self.evaluateButton.setEnabled(True)

    def evaluate(self):
        bans = [str(self.player1Ban.currentText()), str(self.player2Ban.currentText()), str(self.player3Ban.currentText()),
                str(self.player4Ban.currentText()), str(self.player5Ban.currentText()), str(self.player6Ban.currentText()),
                str(self.player7Ban.currentText()), str(self.player8Ban.currentText()), str(self.player9Ban.currentText()),
                str(self.player10Ban.currentText())]
        print('bans', bans, file=sys.stderr)
        picks = [
            (str(self.player1Pick.currentText()), str(self.player1Role.currentText()), 1),
            (str(self.player2Pick.currentText()), str(self.player2Role.currentText()), 1),
            (str(self.player3Pick.currentText()), str(self.player3Role.currentText()), 1),
            (str(self.player4Pick.currentText()), str(self.player4Role.currentText()), 1),
            (str(self.player5Pick.currentText()), str(self.player5Role.currentText()), 1),
            (str(self.player6Pick.currentText()), str(self.player6Role.currentText()), 0),
            (str(self.player7Pick.currentText()), str(self.player7Role.currentText()), 0),
            (str(self.player8Pick.currentText()), str(self.player8Role.currentText()), 0),
            (str(self.player9Pick.currentText()), str(self.player9Role.currentText()), 0),
            (str(self.player10Pick.currentText()), str(self.player10Role.currentText()), 0),
        ]
        print('picks', picks, file=sys.stderr)

        currentState = OrderedDict()
        currentState.update([('s_' + champ, 'A') for champ in self.mode.CHAMPIONS_LABEL])
        currentState.update([('p_' + champ, 'N') for champ in self.mode.CHAMPIONS_LABEL])

        for ban in bans:
            if ban[0] != '.':
                currentState['s_' + ban] = 'N'
        for (pick, role, team) in picks:
            if pick[0] != '.':
                if self.yourTeam == 'B':
                    currentState['s_' + pick] = 'B' if team else 'R'
                else:
                    currentState['s_' + pick] = 'R' if team else 'B'
                currentState['p_' + pick] = role[0]

        data = np.array([self.mode.row_data(currentState, False, True)])
        print(self.mode.row_data(currentState, False, True))
        pred_values = self.network.model.predict(data, batch_size=len(data))[0]
        if self.yourTeam == 'R':
            pred_values = 1 - pred_values
        pred_values *= 100
        self.results.setRowCount(1)
        self.results.setItem(0, 0, QTableWidgetItem('winrate'))
        self.results.setItem(0, 1, QTableWidgetItem('%.2f' % pred_values))

    def generate(self):
        print('generating for:', str(self.yourRole.currentText()), file=sys.stderr)

        bans = [str(self.player1Ban.currentText()), str(self.player2Ban.currentText()), str(self.player3Ban.currentText()),
                str(self.player4Ban.currentText()), str(self.player5Ban.currentText()), str(self.player6Ban.currentText()),
                str(self.player7Ban.currentText()), str(self.player8Ban.currentText()), str(self.player9Ban.currentText()),
                str(self.player10Ban.currentText())]
        print('bans', bans, file=sys.stderr)
        picks = [
            (str(self.player1Pick.currentText()), str(self.player1Role.currentText()), 1),
            (str(self.player2Pick.currentText()), str(self.player2Role.currentText()), 1),
            (str(self.player3Pick.currentText()), str(self.player3Role.currentText()), 1),
            (str(self.player4Pick.currentText()), str(self.player4Role.currentText()), 1),
            (str(self.player5Pick.currentText()), str(self.player5Role.currentText()), 1),
            (str(self.player6Pick.currentText()), str(self.player6Role.currentText()), 0),
            (str(self.player7Pick.currentText()), str(self.player7Role.currentText()), 0),
            (str(self.player8Pick.currentText()), str(self.player8Role.currentText()), 0),
            (str(self.player9Pick.currentText()), str(self.player9Role.currentText()), 0),
            (str(self.player10Pick.currentText()), str(self.player10Role.currentText()), 0),
        ]
        print('picks', picks, file=sys.stderr)
        yourRole = str(self.yourRole.currentText())
        if yourRole == '...':
            print('You need to select a role!', file=sys.stderr)
            return

        currentState = OrderedDict()
        currentState.update([('s_' + champ, 'A') for champ in self.mode.CHAMPIONS_LABEL])
        currentState.update([('p_' + champ, 'N') for champ in self.mode.CHAMPIONS_LABEL])

        for ban in bans:
            if ban[0] != '.':
                currentState['s_' + ban] = 'N'
        for (pick, role, team) in picks:
            if pick[0] != '.':
                if self.yourTeam == 'B':
                    currentState['s_' + pick] = 'B' if team else 'R'
                else:
                    currentState['s_' + pick] = 'R' if team else 'B'
                currentState['p_' + pick] = role[0]

        # print(currentState, file=sys.stderr)
        possibleStates = []
        champions = []
        POSSIBLE_CHAMPS = self.mode.ROLES_CHAMP[yourRole].split(',')
        for champ in POSSIBLE_CHAMPS:
            if currentState['s_' + champ] not in 'AN':  # not available
                continue
            state = OrderedDict(currentState)
            state['s_' + champ] = self.yourTeam
            state['p_' + champ] = yourRole[0]
            possibleStates.append(state)
            champions.append(champ)

        data = []
        for state in possibleStates:
            data.append(self.mode.row_data(state, False, True))

        pred_values = self.network.model.predict(np.array(data), batch_size=len(data))
        best_champs = [(champions[k], 100 * (pred_values[k] if self.yourTeam == 'B' else 1 - pred_values[k])) for k in range(len(champions))]
        best_champs = sorted(best_champs, key=lambda x: x[1], reverse=True)
        print(best_champs, file=sys.stderr)
        self.results.setRowCount(len(best_champs))
        for k in range(len(best_champs)):
            self.results.setItem(k, 0, QTableWidgetItem(best_champs[k][0]))
            self.results.setItem(k, 1, QTableWidgetItem('%.2f' % (best_champs[k][1])))


def run(mode, network):
    app = QApplication(sys.argv)
    App(mode, network)
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(e)


if __name__ == '__main__':
    m = Modes.ABR_TJMCS_Mode()
    run(m, Networks.DenseUniform(m, 5, 256, True))
