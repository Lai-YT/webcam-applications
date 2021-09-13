import cv2
import numpy as np

import screen_brightness_control as sbc
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from lib.brightness_window import BrightnessGui

method = 'wmi'
class BrightnessController(QObject):
    s_exit = pyqtSignal()

    def __init__(self, gui: BrightnessGui):
        super().__init__()
        # Extract the PageWidget to self._pages,
        # other common parts should be accessed through self._gui.
        self._gui = gui
        self.set_brightness(20)
        self.set_button_signal()

    def set_button_signal(self):
        self._gui.start.clicked.connect(self.click_start)
        self._gui.exit.clicked.connect(self.click_exit)
        self._gui.slider.valueChanged.connect(self.value_change)

    def set_brightness(self, brightness: int):
        '''Adjust the brightness of the screen by sliding the slider.'''
        self._gui.label.setText(f'Brightness: {brightness}')
        sbc.set_brightness(brightness, method=method)
        
    def value_change(self):
        '''Change the literal value of brightness.'''
        self.set_brightness(self._gui.slider.value())

    pyqtSlot()
    def capture_image(self):
        '''Capture images and adjust the brightness instantly.'''
        cam = cv2.VideoCapture(0)

        # If exit flag is True, jump out the loop.
        while not self._gui.exit_flag:
            _, frame = cam.read()
            frame = cv2.flip(frame, flipCode=1) # horizontally flip
                
            # Detect the brightness of the frame and adjust the brightness of the screen.
            brightness = self.detect_brightness(frame)
            self.set_brightness(brightness)

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            cv2.imshow('Video Capture', frame)
            cv2.waitKey(50)

        # Close the webcam and emit the exit signal.
            self.set_brightness(20)
            cam.release()
            self.s_exit.emit()
            cv2.destroyAllWindows()

    def get_brightness_percentage(self, frame: np.ndarray) -> int:
        """Returns the percentage of brightness mean."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # hue, saturation, value
        # Value is as known as brightness.
        h, s, v = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
            
        return int(100 * v.mean() / 255)

    def detect_brightness(self, frame: np.ndarray) -> int:
        '''Get the brightness percentage of the frame
            and return the modified brightness value.
        '''
        brightness_percentage = self.get_brightness_percentage(frame)

        # brightness percentage >= 50%
        brightness = int(0.8 * brightness_percentage)
        # 30% < brightness percentage < 50%
        if brightness_percentage < 50:
                brightness = int(2 * (brightness_percentage - 30))
        # brightness percentage < 30%
        brightness = 0 if brightness < 0 else brightness
            
        return brightness

    def click_start(self):
        '''Do things after start button is clicked.'''
        self._gui.slider.hide()
        self._gui.exit.setEnabled(True)
        self._gui.start.setEnabled(False)
        self.capture_image()

    def click_exit(self):
        '''Set exit flag to True.'''
        self._gui.exit_flag = True

    def connect_signal(self):
        '''Connect the exit signal and close the gui.'''
        self.s_exit.connect(self._gui.close)