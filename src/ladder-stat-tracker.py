# -*- coding: utf-8 -*-

import os, time, requests, json, codecs, pickle
from PyQt5 import QtCore
from PyQt5.QtCore import QDir, Qt, QTimer, QSettings
from PyQt5 import QtGui
from PyQt5.QtWidgets import (QApplication, QGroupBox,
    QHBoxLayout,QLabel, QPushButton, QVBoxLayout, QWidget)
        


class LadderStats(QWidget):
    def __init__(self):
        super(LadderStats, self).__init__()

        self.setWindowTitle('Ladder Stat Tracker');

        self.settings = QSettings("com", "app")
        self.restoreGeometry(self.settings.value("geometry", ""))

        self.mainLayout = QVBoxLayout()
        self.scoreLabel = QLabel()
        self.mainLayout.addWidget(self.scoreLabel)

        helpLabel = QLabel("Add this file to your streaming software: " + str(os.path.abspath("scores.txt")))
        self.mainLayout.addWidget(helpLabel)
        
        self.mainLayout.addStretch()
        self.setLayout(self.mainLayout)

        self.resize(475, 150)

        self.scores = {
            'Terr':   { 'Victory': 0, 'Defeat': 0 }, 
            'Prot':   { 'Victory': 0, 'Defeat': 0 }, 
            'Zerg':   { 'Victory': 0, 'Defeat': 0 }, 
        }

        if os.path.exists("names.txt"):
            namesFile = open("names.txt",'rb')
            self.myNames = pickle.load(namesFile)
            namesFile.close()
        else:
            self.myNames = []

        self.inGame = False
        self.timer = QTimer()
        self.timer.timeout.connect(self.goTimer)
        self.timer.start(2500)
        self.update()

    def goTimer(self):
        self.checkSC2()
        self.timer.start(2500)
        self.update()

    def checkSC2(self):
        r = requests.get('http://localhost:6119/game')
        data = r.json()

        if self.inGame == False and ( data['players']==[] or data['players'][0]['result'] == 'Undecided' ) and data['isReplay'] == False: # match started
            self.inGame = True
        elif self.inGame == True and data['players']!=[] and data['players'][0]['result'] != 'Undecided' and data['isReplay'] == False: # match finished
            self.inGame = False
            if data['players'][0]['name'] in self.myNames and data['players'][1]['name'] in self.myNames:
                #  sc2 only tells us the name and barcodes are a thing. common names could also cause stats to 
                #  be recorded incorrectly. only way to get accurate info is asking the user to confirm 
                self.addConfirmMessage(data['players']);
            elif data['players'][0]['name'] not in self.myNames and data['players'][1]['name'] not in self.myNames:
                # we didnt know which player the user was so we have to ask
                self.addConfirmMessage(data['players']);
            else :
                if data['players'][1]['name'] in self.myNames: # if we're player[1], switch the players around
                    tmp = data['players'][0]
                    data['players'][0] = data['players'][1]
                    data['players'][1] = tmp
                # if opponent race is random, ask what race. random race doesnt show in the api.
                self.recordScore(data['players'][1]['race'], data['players'][0]['result']);
            self.update()

    def addConfirmMessage(self, players):
        box = QGroupBox()
        layout = QHBoxLayout()

        label = QLabel('which player were you?')
        layout.addWidget(label)

        button1 = QPushButton(players[0]['race'] + ": " + players[0]['name'] + "(" + players[0]['result'] + ")")
        button1.clicked.connect(lambda: self.handleButton(box, players[1]['race'], players[0]['result'], players[0]['name']))
        layout.addWidget(button1)

        button2 = QPushButton(players[1]['race'] + ": " + players[1]['name'] + "(" + players[1]['result'] + ")")
        button2.clicked.connect(lambda: self.handleButton(box, players[0]['race'], players[1]['result'], players[0]['name']))
        layout.addWidget(button2)
        box.setLayout(layout)
        self.mainLayout.addWidget(box)
        QApplication.alert(self)
        

    def handleButton(self, box, race, result, name = False):
        self.mainLayout.removeWidget(box)
        box.setParent(None)
        self.recordScore(race, result)
        if name != False and name not in self.myNames:
            self.myNames.append(name)
            namesFile = open("names.txt",'wb+')
            pickle.dump(self.myNames, namesFile)
            namesFile.close()

    def addRandomConfirmMessage(self, result):
        box = QGroupBox()
        layout = QHBoxLayout()

        label = QLabel('what race was your opponent playing?')
        layout.addWidget(label)

        button1 = QPushButton('Terran')
        button1.clicked.connect(lambda: self.handleButton(box, 'Terr', result))
        layout.addWidget(button1)
        button1 = QPushButton('Zerg')
        button1.clicked.connect(lambda: self.handleButton(box, 'Zerg', result))
        layout.addWidget(button1)
        button1 = QPushButton('Protoss')
        button1.clicked.connect(lambda: self.handleButton(box, 'Prot', result))
        layout.addWidget(button1)

        box.setLayout(layout)
        self.mainLayout.addWidget(box)

    def recordScore(self, race, result):
        if race == 'random':
            self.addRandomConfirmMessage(result)
        else: 
            self.scores[race][result]=self.scores[race][result]+1
            self.update()

    def update(self):
        score = "vT: %d / %d \nvP: %d / %d\nvZ: %d / %d\n " % (self.scores['Terr']['Victory'], self.scores['Terr']['Defeat'], self.scores['Prot']['Victory'], self.scores['Prot']['Defeat'], self.scores['Zerg']['Victory'], self.scores['Zerg']['Defeat'])
        self.scoreLabel.setText(score)
        scoreFile = open('scores.txt', 'w')
        scoreFile.write(score)
        scoreFile.close()
        scoreFileJson = open('scores.json', 'w')
        scoreFileJson.write(json.dumps(self.scores))
        scoreFileJson.close()

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        QWidget.closeEvent(self, event)

if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    LadderStats = LadderStats()
    LadderStats.show()
    sys.exit(app.exec_())