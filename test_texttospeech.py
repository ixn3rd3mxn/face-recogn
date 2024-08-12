from gtts import gTTS
import os

tts = gTTS(text='สวัสดี นายอีซอมอะไรอยู่ ', lang='th')
tts.save('hello-thai.mp3')
os.system('hello-thai.mp3')