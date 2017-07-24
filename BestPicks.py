import configparser
import sys
from PyQt5 import QtGui
from PyQt5.QtWidgets import *

config = configparser.ConfigParser()
config.read('config.ini')
CHAMPIONS = ['...']
CHAMPIONS.extend(sorted(config['PARAMS']['sortedChamps'].split(',')))
ROLES = ['...', 'Top', 'Jungle', 'Mid', 'Carry', 'Support']


class App(QDialog):
    def __init__(self):
        super().__init__()
        self.title = 'LoLAnalyzer'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 100
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

    def generate(self):
        pass


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
