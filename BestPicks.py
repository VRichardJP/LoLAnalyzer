# Evaluate the best pick for the given role and team

import os
import sys
from PyQt5.QtWidgets import *
from collections import OrderedDict

import Modes
import Networks

sys._excepthook = sys.excepthook


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
    # noinspection PyArgumentList
    def __init__(self, mode, network):
        super().__init__()
        self.title = 'LoLAnalyzer'
        self.left = 10
        self.top = 10
        self.width = 660
        self.height = 400
        self.mode = mode
        self.network = network

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
        yourTeamLayout.addWidget(self.player1Pick, 0, 0)
        self.player1Role = QComboBox()
        self.player1Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player1Role, 0, 1)
        self.player2Pick = QComboBox()
        self.player2Pick.addItems(self.mode.BP_CHAMPIONS)
        yourTeamLayout.addWidget(self.player2Pick, 1, 0)
        self.player2Role = QComboBox()
        self.player2Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player2Role, 1, 1)
        self.player3Pick = QComboBox()
        self.player3Pick.addItems(self.mode.BP_CHAMPIONS)
        yourTeamLayout.addWidget(self.player3Pick, 2, 0)
        self.player3Role = QComboBox()
        self.player3Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player3Role, 2, 1)
        self.player4Pick = QComboBox()
        self.player4Pick.addItems(self.mode.BP_CHAMPIONS)
        yourTeamLayout.addWidget(self.player4Pick, 3, 0)
        self.player4Role = QComboBox()
        self.player4Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player4Role, 3, 1)
        self.player5Pick = QComboBox()
        self.player5Pick.addItems(self.mode.BP_CHAMPIONS)
        yourTeamLayout.addWidget(self.player5Pick, 4, 0)
        self.player5Role = QComboBox()
        self.player5Role.addItems(self.mode.BP_ROLES)
        yourTeamLayout.addWidget(self.player5Role, 4, 1)
        yourTeamGB.setLayout(yourTeamLayout)
        mainBoxLayout.addWidget(yourTeamGB, 1, 0)

        # Ennemy team picks Layout
        ennemyTeamGB = QGroupBox('Ennemy Team')
        ennemyTeamLayout = QVBoxLayout()
        self.player6Pick = QComboBox()
        self.player6Pick.addItems(self.mode.BP_CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player6Pick)
        self.player7Pick = QComboBox()
        self.player7Pick.addItems(self.mode.BP_CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player7Pick)
        self.player8Pick = QComboBox()
        self.player8Pick.addItems(self.mode.BP_CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player8Pick)
        self.player9Pick = QComboBox()
        self.player9Pick.addItems(self.mode.BP_CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player9Pick)
        self.player10Pick = QComboBox()
        self.player10Pick.addItems(self.mode.BP_CHAMPIONS)
        ennemyTeamLayout.addWidget(self.player10Pick)
        ennemyTeamGB.setLayout(ennemyTeamLayout)
        mainBoxLayout.addWidget(ennemyTeamGB, 1, 2)

        # Best picks Layout
        bestPicksGB = QGroupBox('Best Picks')
        bestPicksLayout = QGridLayout()
        yourTeamLabel = QLabel()
        yourTeamLabel.setText('Your team:')
        bestPicksLayout.addWidget(yourTeamLabel, 0, 0)
        self.yourTeam = QComboBox()
        self.yourTeam.addItems(self.mode.BP_TEAMS)
        bestPicksLayout.addWidget(self.yourTeam, 0, 1)
        self.evaluateButton = QPushButton('Wait...')
        self.evaluateButton.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self.evaluateButton.clicked.connect(lambda: self.evaluate())
        bestPicksLayout.addWidget(self.evaluateButton, 0, 2)
        yourRoleLabel = QLabel()
        yourRoleLabel.setText('Your role:')
        bestPicksLayout.addWidget(yourRoleLabel, 1, 0)
        self.yourRole = QComboBox()
        self.yourRole.addItems(self.mode.BP_ROLES)
        bestPicksLayout.addWidget(self.yourRole, 1, 1)
        self.generateButton = QPushButton('Wait...')
        self.generateButton.setEnabled(False)
        # noinspection PyUnresolvedReferences
        self.generateButton.clicked.connect(lambda: self.generate())
        bestPicksLayout.addWidget(self.generateButton, 1, 2)

        self.results = QTableWidget()
        # self.results.setRowCount(4)
        self.results.setColumnCount(2)
        self.results.horizontalHeader().hide()
        self.results.verticalHeader().hide()
        bestPicksLayout.addWidget(self.results, 2, 0, 1, 3)

        bestPicksGB.setLayout(bestPicksLayout)
        mainBoxLayout.addWidget(bestPicksGB, 1, 1)

        # Centering window
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())

        self.show()

        self.buildNetwork()

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
        print('generating for:', str(self.yourRole.currentText()), file=sys.stderr)
        currentState = OrderedDict([(champ, 'A') for champ in self.mode.CHAMPIONS_LABEL])
        bans = [str(self.player1Ban.currentText()), str(self.player2Ban.currentText()), str(self.player3Ban.currentText()),
                str(self.player4Ban.currentText()), str(self.player5Ban.currentText()), str(self.player6Ban.currentText()),
                str(self.player7Ban.currentText()), str(self.player8Ban.currentText()), str(self.player9Ban.currentText()),
                str(self.player10Ban.currentText())]
        print('bans', bans, file=sys.stderr)
        picks = [(str(self.player1Pick.currentText()), str(self.player1Role.currentText())),
                 (str(self.player2Pick.currentText()), str(self.player2Role.currentText())),
                 (str(self.player3Pick.currentText()), str(self.player3Role.currentText())),
                 (str(self.player4Pick.currentText()), str(self.player4Role.currentText())),
                 (str(self.player5Pick.currentText()), str(self.player5Role.currentText())),
                 (str(self.player6Pick.currentText()), 'Opp'), (str(self.player7Pick.currentText()), 'Opp'),
                 (str(self.player8Pick.currentText()), 'Opp'), (str(self.player9Pick.currentText()), 'Opp'),
                 (str(self.player10Pick.currentText()), 'Opp')]
        print('picks', picks, file=sys.stderr)
        for ban in bans:
            if ban[0] != '.':
                currentState[ban] = 'B'
        for (pick, role) in picks:
            if pick[0] != '.' and role[0] in self.mode.CHAMPIONS_STATUS:
                currentState[pick] = role[0]

        yourTeam = str(self.yourTeam.currentText())
        if yourTeam == '...':
            print('You need to select a team!', file=sys.stderr)
            return

        data = []
        row_data = []
        row_data.extend([1 if currentState[self.mode.CHAMPIONS_LABEL[k]] == s else 0 for k in range(len(self.mode.CHAMPIONS_LABEL)) for s in
                         self.mode.CHAMPIONS_STATUS])
        row_data.extend(self.mode.PATCH)
        if type(self.mode) in [Modes.ABOTJMCS_Mode, Modes.ABOT_Mode]:
            row_data.append(0 if yourTeam == 'Blue' else 1)
        data.append(row_data)

        pred_values = self.network.model.predict(data, batch_size=len(data))
        self.results.setRowCount(1)
        self.results.setItem(0, 0, QTableWidgetItem('winrate'))
        self.results.setItem(0, 1, QTableWidgetItem('%.2f' % (pred_values[0] * 100)))

    def generate(self):
        print('generating for:', str(self.yourRole.currentText()), file=sys.stderr)
        currentState = OrderedDict([(champ, 'A') for champ in self.mode.CHAMPIONS_LABEL])
        bans = [str(self.player1Ban.currentText()), str(self.player2Ban.currentText()), str(self.player3Ban.currentText()),
                str(self.player4Ban.currentText()), str(self.player5Ban.currentText()), str(self.player6Ban.currentText()),
                str(self.player7Ban.currentText()), str(self.player8Ban.currentText()), str(self.player9Ban.currentText()),
                str(self.player10Ban.currentText())]
        print('bans', bans, file=sys.stderr)
        picks = [(str(self.player1Pick.currentText()), str(self.player1Role.currentText())),
                 (str(self.player2Pick.currentText()), str(self.player2Role.currentText())),
                 (str(self.player3Pick.currentText()), str(self.player3Role.currentText())),
                 (str(self.player4Pick.currentText()), str(self.player4Role.currentText())),
                 (str(self.player5Pick.currentText()), str(self.player5Role.currentText())),
                 (str(self.player6Pick.currentText()), 'Opp'), (str(self.player7Pick.currentText()), 'Opp'),
                 (str(self.player8Pick.currentText()), 'Opp'), (str(self.player9Pick.currentText()), 'Opp'),
                 (str(self.player10Pick.currentText()), 'Opp')]
        print('picks', picks, file=sys.stderr)
        for ban in bans:
            if ban[0] != '.':
                currentState[ban] = 'B'
        for (pick, role) in picks:
            if pick[0] != '.' and role[0] in self.mode.CHAMPIONS_STATUS:
                currentState[pick] = role[0]

        yourRole = str(self.yourRole.currentText())
        if yourRole == '...':
            print('You need to select a role!', file=sys.stderr)
            return
        yourTeam = str(self.yourTeam.currentText())
        if yourTeam == '...':
            print('You need to select a team!', file=sys.stderr)
            return

        # print(currentState, file=sys.stderr)
        possibleStates = []
        champions = []
        POSSIBLE_CHAMPS = self.mode.ROLES_CHAMP[yourRole].split(',')
        for champ in POSSIBLE_CHAMPS:
            if currentState[champ] != 'A':
                continue
            state = OrderedDict(currentState)
            state[champ] = yourRole[0]
            possibleStates.append(state)
            champions.append(champ)

        data = []

        for state in possibleStates:
            row_data = []
            row_data.extend([1 if state[self.mode.CHAMPIONS_LABEL[k]] == s else 0 for k in range(len(self.mode.CHAMPIONS_LABEL)) for s in
                             self.mode.CHAMPIONS_STATUS])
            row_data.extend(self.mode.PATCH)
            if type(self.mode) in [Modes.ABOTJMCS_Mode, Modes.ABOT_Mode, Modes.OTJMCS_Mode]:
                row_data.append(0 if yourTeam == 'Blue' else 1)
            data.append(row_data)

        pred_values = self.network.model.predict(data, batch_size=len(data))
        best_champs = [(champions[k], pred_values[k] if yourTeam == 'Blue' else 1 - pred_values[k]) for k in range(len(champions))]
        best_champs = sorted(best_champs, key=lambda x: x[1], reverse=True)

        print(best_champs, file=sys.stderr)
        self.results.setRowCount(len(best_champs))
        for k in range(len(best_champs)):
            self.results.setItem(k, 0, QTableWidgetItem(best_champs[k][0]))
            self.results.setItem(k, 1, QTableWidgetItem('%.2f' % (best_champs[k][1] * 100)))


def run(mode, network):
    app = QApplication(sys.argv)
    App(mode, network)
    try:
        sys.exit(app.exec_())
    except Exception as e:
        print(e)


if __name__ == '__main__':
    m = Modes.BR_Mode()
    run(m, Networks.DenseUniform(m, 5, 256, True))
