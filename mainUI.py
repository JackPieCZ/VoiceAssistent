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
CACHE_PATH = os.path.join(CWD, "cache")                 # cache folder for audio files
AUDIO_PATH = os.path.join(CWD, 'audio')
if not os.path.exists(CACHE_PATH):
	os.mkdir(CACHE_PATH)

emojis = {
	100:"applause",
	101:"dancing",
	102:"deal_with_it",
	103:"excited",
	104:"lol",
	105:"loving",
	106:"no",
	107:"shocked",
	108:"thinking",
	109:"yes"
		}


def deleteCache(cache):		# pro každou cache složku zkontrolovat jestli existuje, pokud ano, pokusit se odstranit
	if os.path.exists(cache):
		try: shutil.rmtree(cache)
		except Exception: 		# pokud z nějakého důvodu odstranit nelze (uživatel ji má otevřenou v prohlížeči souborů nebo Windows do ní právě zapisuje)
			print(f"Cleaning cache failed when closing - {cache}")	# napsat chybovou hlášku a zkusit za vteřinu znova

class User:
	name = ""
	def setName(self, name):
		self.name = name

class Asistant:
	name = ""
	def setName(self, name):
		self.name = name

class GUI_Instance(QWidget):
	input_signal = pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.UI()
		self.setMinimumHeight(712)
		self.move(435,120)
		self.setupThread()
	
	def closeEvent(self, event):    # spustí se při zavření okna nebo programu
		event.accept()
		deleteCache(CACHE_PATH)			# odstranit cache

	def UI(self):	# uživatelské rozhraní
		self.groupBox = QGroupBox(self)
		gridLayout = QGridLayout()

		self.emoji = QLabel(self)
		self.emoji.setAlignment(Qt.AlignCenter)
		self.setEmoji("excited")
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
		self.recordButton.setStyleSheet(
			"color: rgb(219,35,35);"
			"border-color: rgb(219,35,35);")
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


		self.groupBox.setLayout(gridLayout)
		self.groupBox.setStyleSheet("background-color: rgb(10,10,10)")
		self.vbox = QVBoxLayout()
		self.vbox.addWidget(self.groupBox)
		self.setLayout(self.vbox)
		self.setWindowTitle("Voice Assistant")
		self.show()
	
	def setEmoji(self,emotion):
		self.gif = QMovie(os.path.join(EMOJI_PATH, str(emotion)+".gif"))
		self.emoji.setMovie(self.gif)
		self.gif.start()
	
	def updateUI(self,input_string, output_string, emoji_int):
		if input_string:
			self.inputLabel.setText("You >> " + input_string)
		if output_string:
			self.outputLabel.setText("Asistant >> "+ output_string)
		if input_string or output_string:
			self.resetVisibilities()
		if emoji_int >= 100:
			self.setEmoji(emojis[emoji_int])
		
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
		self.input_signal.emit(0)

	def record(self):
		self.input_signal.emit(1)
		self.setEmoji(emojis[101])
		self.recordButton.setVisible(False)
		self.exitButton.setDisabled(True)
		self.inputLabel.setVisible(False)
		self.outputLabel.setVisible(False)
		self.listeningGif.setVisible(True)
		self.inputLabel.clear()
		self.outputLabel.clear()
	
	def exitProgram(self):
		self.input_signal.emit(99)
		self.inputLabel.clear()
		QTimer.singleShot(2000, lambda: self.close())

class VoiceProcessing(QObject):
	output_signal = pyqtSignal(str,str,int)

	@pyqtSlot(int)
	def select_action(self, command):
		if command == 0:
			self.init()
		elif command == 1:
			self.record()
		elif command == 99:
			self.engine_speak("Good bye "+self.person_obj.name+"!",109)
		else:
			print("unknown command")

	def init(self):
		self.r = sr.Recognizer() # initialise a recogniser
		self.person_obj = User()
		self.asis_obj = Asistant()
		self.asis_obj.name = "Qwerty"
		self.person_obj.name = ""
		print("initilized")

	def record(self, ask=""):	# listen for audio and convert it to text:
		print("recording")
		with sr.Microphone() as source: # microphone as source
			if ask:
				Thread(target=self.engine_speak, args=([ask],0)).start()
			self.playSound(os.path.join(AUDIO_PATH, 'Recording.wav'))
			audio = self.r.listen(source, 5, 5)  # listen for the audio for 5 secs
			self.output_signal.emit("","",108)
			voice_data = ""
			try:
				voice_data = str(self.r.recognize_google(audio))
			except sr.UnknownValueError or sr.WaitTimeoutError: # recognizer didn't understand
				self.engine_speak("I did not get that", 107)
			except sr.RequestError: # recognizer is not connected
				self.engine_speak("Sorry, the service is down. Try again later!",102)
			if voice_data:
				print("Your input >> ", voice_data.lower())
				self.output_signal.emit(voice_data.capitalize(),"",0)
				self.respond(voice_data.lower())
	
	def engine_speak(self, text_string, emoji_int):
		tts = gtts.gTTS(text=(text_string), lang='en', tld='ae') # text to speech(voice)
		audio_file = os.path.join(CACHE_PATH, ('audio_' + str(random.randint(1,200000)) + '.mp3'))
		tts.save(audio_file)
		self.playSound(audio_file)
		self.output_signal.emit("", text_string,emoji_int)
		print(self.asis_obj.name + " >> ", text_string)
	
	def playSound(self, audio_file):
		Thread(target=playsound.playsound, args=[audio_file]).start()
	
	def respond(self, voice_data):
		#1: name
		if any(string in voice_data for string in ["what is your name","what's your name","tell me your name"]):
			if self.person_obj.name:
				self.engine_speak(f"My name is {self.asis_obj.name}, {self.person_obj.name}.",104) #gets users name from voice input
			else:
				self.engine_speak(f"My name is {self.asis_obj.name}. What's your name?",104) #incase you haven't provided your name.
		elif any(string in voice_data for string in ["my name is"]):
			person_name = voice_data.split("is")[-1].strip().capitalize()
			self.engine_speak(f"Okay, i will remember that, {person_name}.",109)
			self.person_obj.setName(person_name) # remember name in person object
		
		elif any(string in voice_data for string in ["what is my name","what's my name"]):
			self.engine_speak(f"Your name must be {self.person_obj.name}.", 108)
		
		elif any(string in voice_data for string in ["your name should be"]):
			asis_name = voice_data.split("be ")[-1].strip().capitalize()
			self.engine_speak(f"Okay, i will remember that my name is {asis_name}.",109)
			self.asis_obj.setName(asis_name) # remember name in asistant object
		
		# 2: greeting
		elif any(string in voice_data for string in ["how are you","how are you doing"]):
			self.engine_speak(f"I'm very well, thanks for asking {self.person_obj.name}.", 101)
		
		# 3: time
		elif any(string in voice_data for string in ["what's the time","tell me the time","what time is it","what's the current time"]):
			current_time = ctime().split(" ")[3].split(":")[0:2]
			if current_time[0] == "00":
				hours = '12'
			else:
				hours = current_time[0]
			minutes = current_time[1]
			current_time = hours + " hours and " + minutes + " minutes"
			self.engine_speak(f"It's {current_time}.",109)
		
		# 4: get (stock) price
		elif "price of" in voice_data:
			search_term = (voice_data.split("of")[-1])[1:]
			url = "https://google.com/search?q=" + search_term +" price"
			webbrowser.get().open(url)
			self.engine_speak("Here's the current price for " + search_term + " according to Google", 103)
		
		# 5: weather
		elif "weather" in voice_data:
			search_term = (voice_data.split("for")[-1])[1:]
			url = "https://www.google.com/search?q=weather "+(search_term)
			webbrowser.get().open(url)
			self.engine_speak(f"Here's the current forcast for {search_term}.",107)
		
		# 6: Current locations
		elif any(string in voice_data for string in ["what is my exact location","my location", "where am i"]):
			url = "https://www.google.com/maps/search/Where+am+I+?/"
			webbrowser.get().open(url)
			Ip_info = requests.get('https://api.ipdata.co?api-key=193c911867c19a6f680be545035399aabae13e2c80ee868d5519beba').json()
			self.engine_speak(f"You must be somewhere in {Ip_info['region']} in {Ip_info['country_name']}.",104) 


		# 97: search google
		elif "search for" in voice_data and "youtube" not in voice_data:
			search_term = (voice_data.split("for")[-1])[1:]
			url = "https://google.com/search?q=" + search_term
			webbrowser.get().open(url)
			self.engine_speak(f"Here is what I found for {search_term} on Google",103)
		
		elif "search on google" in voice_data:
			search_term = (voice_data.split("for")[-1])[1:]
			url = "https://google.com/search?q=" + search_term
			webbrowser.get().open(url)
			self.engine_speak(f"Here is what I found for {search_term} on Google",103)
		
		# 98: search youtube
		elif "search on youtube" in voice_data:
			search_term = (voice_data.split("for")[-1])[1:]
			search_term = search_term.replace("on youtube","").replace("search","")
			url = "https://www.youtube.com/results?search_query=" + search_term
			webbrowser.get().open(url)
			self.engine_speak(f"Here is what I found for {search_term} on Youtube",103)
		
		
		# 99: greeting
		elif any(string in voice_data for string in ["hey","hi","hello","whatsapp"]):
			greetings = [
				"Hey, how can I help you " + self.person_obj.name + "?",
				"Hey, what's up " + self.person_obj.name + "!",
				"Hi! I'm listening " + self.person_obj.name + "...",
				"Hi! How can I help you " + self.person_obj.name + "?",
				"Hello friend " + self.person_obj.name + "!"]
			self.engine_speak(random.choice(greetings),105)

		# didn't recognize
		else:
			self.engine_speak("I'm not quite sure what you meant...",108)

#######################################

if __name__ == "__main__":
	App = QApplication(sys.argv)
	gui = GUI_Instance()                						# vytvoří instanci GUI
	qt_material.apply_stylesheet(App, theme="dark_blue.xml")	# aplikuje tmavomodrý vzhled
	App.setFont(QFont("Century Gothic", 8))						# nastaví font aplikace na Century Gothic
	sys.exit(App.exec_())