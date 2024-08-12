import sys
from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from PyQt6 import uic
import time

class MyApp(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("SeagullPage1.ui",self)
        self.setWindowTitle("SEAGULL IDENTIFIER")


        self.bBlackHead.clicked.connect(lambda:self.openNewPage(self.bBlackHead))
        self.bWhiteHead.clicked.connect(lambda:self.openNewPage(self.bWhiteHead))  

    def openNewPage(self,b):
        
        NewPage = b.text()
        uic.loadUi(f"{NewPage}.ui",self)
        self.show
    
    
class WhiteHead(QMainWindow):
    def __init__(self):
        super().__init__

        self.setWindowTitle("SEAGULL IDENTIFIER2") 
            
        self.BlackFeetButton.clicked.connect(lambda:self.openNewPage(self.BlackFeetButton))
        self.PinkFeetButton.clicked.connect(lambda:self.openNewPage(self.PinkFeetButton))
        self.YellowFeetButton.clicked.connect(lambda:self.openNewPage(self.YellowFeetButton))   