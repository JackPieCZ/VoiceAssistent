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
from PyQt5.QtCore import  QThread, pyqtSignal, pyqtSlot, Qt, QObject, QTimer, QSize
import qt_material
from threading import Thread

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
			"excitied",
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

def there_exists(terms, voice_data):
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
	input_signal = pyqtSignal(str)

	def __init__(self):
		super().__init__()
		self.UI()
		self.setMinimumHeight(712)
		self.move(435,120)
		self.setupThread()
	
	def closeEvent(self, event):    # spustí se při zavření okna nebo programu
		event.accept()
		deleteCache(AUDIO_PATH)			# odstranit cache

	def UI(self):	# uživatelské rozhraní
		gridLayout = QGridLayout()

		self.emoji = QLabel(self)
		self.emoji.setAlignment(Qt.AlignCenter)
		self.setEmoji("excitied")
		gridLayout.addWidget(self.emoji,1,0,1,1)

		self.inputLabel = QLabel("")
		self.inputLabel.setAlignment(Qt.AlignCenter)
		self.inputLabel.setFont(QFont("Century Gothic",13))
		gridLayout.addWidget(self.inputLabel,2,0,1,1)

		self.outputLabel = QLabel("")
		self.outputLabel.setAlignment(Qt.AlignCenter)
		self.outputLabel.setFont(QFont("Century Gothic",13))
		gridLayout.addWidget(self.outputLabel,3,0,1,1)

		self.recordButton = QPushButton()
		#self.recordButton.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
		self.recordButton.setText("Record")
		self.recordButton.clicked.connect(self.record)
		gridLayout.addWidget(self.recordButton,4,0,1,1)

		self.listeningGif = QLabel(self)
		self.listeningGif.setAlignment(Qt.AlignCenter)
		self.listeninggif = QMovie("listening.gif")
		self.listeninggif.setScaledSize(QSize(200,150))
		self.listeningGif.setMovie(self.listeninggif)
		self.listeninggif.start()
		self.listeningGif.setVisible(False)
		gridLayout.addWidget(self.listeningGif,5,0,1,1)

		self.exitButton = QPushButton()
		self.exitButton.setText("Exit")
		self.exitButton.clicked.connect(self.exitProgram)
		gridLayout.addWidget(self.exitButton,6,0,1,1)

		self.setLayout(gridLayout)
		self.setWindowTitle("Voice Assistant")
		self.show()

		self.timer = QTimer(self)
		self.timer.setInterval(3000)
		self.timer.timeout.connect(self.setRandomEmoji)
		#self.timer.start()
	
	def setRandomEmoji(self):
		self.setEmoji(random.choice(emojis))
	
	def setEmoji(self,emotion):
		self.gif = QMovie(os.path.join(EMOJI_PATH, str(emotion)+".gif"))
		self.emoji.setMovie(self.gif)
		self.gif.start()
	
	def updateUI(self,input_string, output_string):
		self.resetVisibilities()
		if input_string:
			self.inputLabel.setText(">> " + input_string)
		if output_string:
			self.outputLabel.setText("Asistant >> "+ output_string)
		if output_string == "I did not get that.":
			self.setEmoji("shocked")
			QTimer.singleShot(3250, lambda: self.setEmoji("excitied"))
		
	
	def resetVisibilities(self):
		self.listeningGif.setVisible(False)
		self.recordButton.setVisible(True)
		self.inputLabel.setVisible(True)
		self.outputLabel.setVisible(True)
		self.recordButton.setDisabled(False)
		self.exitButton.setDisabled(False)

	def setupThread(self):
		self.worker = VoiceProcessing()
		self.worker_thread = QThread()
		self.worker.moveToThread(self.worker_thread)
		self.worker_thread.start()
		self.worker.output_signal.connect(self.updateUI)
		self.input_signal.connect(self.worker.select_action)
		self.input_signal.emit("init")

	def record(self):
		self.input_signal.emit("rec")
		self.recordButton.setVisible(False)
		self.exitButton.setDisabled(True)
		self.inputLabel.setVisible(False)
		self.outputLabel.setVisible(False)
		self.listeningGif.setVisible(True)
		self.setEmoji("dancing")
		self.inputLabel.clear()
		self.outputLabel.clear()
	
	def exitProgram(self):
		self.input_signal.emit("bye")
		QTimer.singleShot(2000, lambda: self.close())

class VoiceProcessing(QObject):
	output_signal = pyqtSignal(str,str)

	@pyqtSlot(str)
	def select_action(self, command):
		if command == "init":
			self.init()
		elif command == "rec":
			self.record("Recording.")
		elif command == "bye":
			self.engine_speak("Good bye.")
		else:
			print("unknown command")

	def init(self):
		self.r = sr.Recognizer() # initialise a recogniser
		self.person_obj = User()
		self.asis_obj = Asistant()
		self.asis_obj.name = "Assistant"
		self.person_obj.name = ""
		print("initilized")

	def record(self, ask=""):	# listen for audio and convert it to text:
		print("recording")
		with sr.Microphone() as source: # microphone as source
			if ask:
				self.engine_speak(ask)
			audio = self.r.listen(source, 5, 5)  # listen for the audio for 5 secs
			print("Done listening")
			voice_data = ""
			try:
				voice_data = str(self.r.recognize_google(audio))
			except sr.UnknownValueError or sr.WaitTimeoutError: # recognizer didn't understand
				self.engine_speak("I did not get that.")
			except sr.RequestError: # recognizer is not connected
				self.engine_speak("Sorry, the service is down. Try again later!")
			if voice_data:
				print("Your input >> ", voice_data.lower())
				self.engine_speak(">> "+voice_data.lower()+ "")
				return voice_data.lower()
	
	def engine_speak(self, text_string):
		tts = gtts.gTTS(text=text_string, lang='en', tld='ae') # text to speech(voice)
		audio_file = os.path.join(AUDIO_PATH, ('audio_' + str(random.randint(1,200000)) + '.mp3'))
		tts.save(audio_file)
		self.playSound(audio_file)
		if text_string != ("Recording." or "Good bye."):
			self.output_signal.emit("", text_string)
			print(self.asis_obj.name + " >> ", text_string)
	
	def playSound(self, audio_file):
		Thread(target=(playsound.playsound), args = [audio_file]).start()

#######################################
if __name__ == "__main__":
	App = QApplication(sys.argv)
	gui = GUI_Instance()                						# vytvoří instanci GUI
	qt_material.apply_stylesheet(App, theme="dark_blue.xml")	# aplikuje tmavomodrý vzhled
	App.setFont(QFont("Century Gothic", 8))						# nastaví font aplikace na Century Gothic
	sys.exit(App.exec_())