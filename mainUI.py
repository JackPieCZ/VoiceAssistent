# Essential libraries
import speech_recognition as sr # recognise speech
import playsound # to play an audio file
import gtts # google text to speech
import os # to remove created audio files
import shutil
import sys
from PyQt5.QtWidgets import (
	QMainWindow, QApplication, QWidget, QHBoxLayout, QVBoxLayout, QSpacerItem, QSizePolicy, QStackedWidget, QGroupBox,
	QGridLayout, QLabel, QToolButton, QPushButton)
from PyQt5.QtGui import QFont, QIcon, QMovie, QPixmap
from PyQt5.QtCore import  QThread, pyqtSignal, pyqtSlot, Qt, QObject, QTimer
import qt_material

# Libraries for different functions of voice assistant
import random
from time import ctime # get time details
import webbrowser # open browser
import time
from PIL import Image
import pyautogui #screenshot
import bs4 as bs
import urllib.request
import requests

CWD = os.path.dirname(os.path.realpath(__file__))       # current folder
EMOJI_PATH = os.path.join(CWD, "emojis")				# emojis folder
AUDIO_PATH = os.path.join(CWD, "audio")                 # cache folder for audio files
if not os.path.exists(AUDIO_PATH):
	os.mkdir(AUDIO_PATH)

emojis = [
			"applause",
			"dancing",
			"deal_with_it",
			"excited",
			"lol",
			"loving",
			"no",
			"shocked",
			"thinking",
			"yes"
		]


def deleteCache(cache):		# pro každou cache složku zkontrolovat jestli existuje, pokud ano, pokusit se odstranit
	if os.path.exists(cache):
		try: shutil.rmtree(cache)
		except Exception: 		# pokud z nějakého důvodu odstranit nelze (uživatel ji má otevřenou v prohlížeči souborů nebo Windows do ní právě zapisuje)
			print(f"Cleaning cache failed when closing - {cache}")	# napsat chybovou hlášku a zkusit za vteřinu znova

def there_exists(terms):
	for term in terms:
		if term in voice_data:
			return True

class User:
	name = ""
	def setName(self, name):
		self.name = name

class Asistant:
	name = ""
	def setName(self, name):
		self.name = name

class GUI_Instance(QWidget):
	reaction_requested = pyqtSignal(str)

	def __init__(self):
		super().__init__()
		self.UI()
		self.setMinimumSize(1280, 720)
		self.move(435,120)
		self.setupThread()
	
	def closeEvent(self, event):    # spustí se při zavření okna nebo programu
		event.accept()
		deleteCache(AUDIO_PATH)			# odstranit cache

	def UI(self):	# uživatelské rozhraní
		gridLayout = QGridLayout()

		self.emoji = QLabel(self)
		self.emoji.setAlignment(Qt.AlignCenter)
		self.emoji.setFixedSize(480,480)
		self.setEmoji("dancing")
		gridLayout.addWidget(self.emoji,1,0)

		self.status = QLabel("Status")
		self.status.setAlignment(Qt.AlignCenter)
		self.status.setFont(QFont("Century Gothic",13))
		gridLayout.addWidget(self.status,2,0)

		self.recordButton = QPushButton()
		#self.recordButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.recordButton.setText("Record")
		self.recordButton.clicked.connect(self.record)
		gridLayout.addWidget(self.recordButton,3,0)

		self.setLayout(gridLayout)
		self.setWindowTitle("Voice Assistant")
		self.show()
	
	def setEmoji(self,emotion):
		self.gif = QMovie(os.path.join(EMOJI_PATH, str(emotion)+".gif"))
		self.emoji.setMovie(self.gif)
		self.gif.start()
	
	def updateUI(self,string):
		pass

	def setupThread(self):
		self.worker = VoiceProcessing()
		self.worker_thread = QThread()
		self.worker.moveToThread(self.worker_thread)
		self.worker_thread.start()
		self.worker.response.connect(self.updateUI)
		self.reaction_requested.connect(self.worker.select_action)
		self.reaction_requested.emit("init")

	def record(self):
		self.reaction_requested.emit("rec")

class VoiceProcessing(QObject):
	response = pyqtSignal(str)

	@pyqtSlot(str)
	def select_action(self, command):
		if command == "init":
			self.init()
		elif command == "rec":
			self.record()
	def init(self):
		r = sr.Recognizer() # initialise a recogniser
		person_obj = User()
		asis_obj = Asistant()
		asis_obj.name = 'kiki'
		person_obj.name = ""
		print("initilized")

	def record(self):
		print("recording")

#######################################
if __name__ == "__main__":
	App = QApplication(sys.argv)
	gui = GUI_Instance()                						# vytvoří instanci GUI
	qt_material.apply_stylesheet(App, theme="dark_blue.xml")	# aplikuje tmavomodrý vzhled
	App.setFont(QFont("Century Gothic", 8))						# nastaví font aplikace na Century Gothic
	sys.exit(App.exec_())