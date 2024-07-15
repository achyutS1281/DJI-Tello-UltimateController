import threading
import time

from djitellopy import Tello
import speech_recognition as sr


class Speech_Controller:

    def __init__(self, tello: Tello):
        self.drone = tello
        self.text = ""
        self.thread = None
        self.stop = False
        self.running = False

    def start(self):
        def on_speech(spokenText):
            if spokenText == "takeoff" or spokenText == "take off":
                self.drone.takeoff()
            elif spokenText == "forward":
                self.drone.move_forward(50)
            elif spokenText == "back":
                self.drone.move_back(50)
            elif spokenText == "right":
                self.drone.move_right(50)
            elif spokenText == "left":
                self.drone.move_left(50)
            elif spokenText == "flip left" or spokenText == "flipleft":
                self.drone.flip('l')
            elif spokenText == "flip right" or spokenText == "flipright":
                self.drone.flip('r')
            elif spokenText == "flip back" or spokenText == "flipback":
                self.drone.flip('b')
            elif spokenText == "flip forward" or spokenText == "flipforward":
                self.drone.flip('f')
            elif spokenText == "rotate right" or spokenText == "rotateright":
                self.drone.rotate_clockwise(50)
            elif spokenText == "rotate left" or spokenText == "rotateleft":
                self.drone.rotate_counter_clockwise(50)
            elif spokenText == "up":
                self.drone.move_up(50)
            elif spokenText == "down":
                self.drone.move_down(50)
            elif spokenText == "land":
                self.drone.land()

        def begin():
            r = sr.Recognizer()
            while True:
                with sr.Microphone() as mic:
                    r.adjust_for_ambient_noise(source=mic, duration=1)
                    if self.stop:
                        break
                    print("say something:")
                    audio = r.listen(source=mic, phrase_time_limit=2)
                    if self.stop:
                        break
                self.text = eval(r.recognize_vosk(audio_data=audio, language="en"))["text"]
                print(self.text)
                if self.stop:
                    break
                on_speech(self.text)

        if not self.running:
            self.thread = threading.Thread(target=begin).start()
            self.running = True

    def stop(self):
        if self.running:
            self.stop = True
            self.running = False
