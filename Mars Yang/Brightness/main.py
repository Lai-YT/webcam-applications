import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import cv2
import numpy as np
import screen_brightness_control as sbc

method = 'wmi'

class SliderDemo(QWidget):
    s_exit = pyqtSignal()

    def __init__(self, parent=None):
        super(SliderDemo, self).__init__(parent)

        self.setWindowTitle("Utimate Brightness Detector")
        self.resize(450, 300)
        self.setWindowIcon(QIcon("sun.ico"))
        self.layout = QVBoxLayout()
        self.set_slider()
        self.set_button()
        self.set_brightness(20)
        # Initialize exit flag.
        self.exit_flag = False

    def set_slider(self):
        '''Set a horizontal slider and a label on the window.'''
        self.label = QLabel("Brightness: 10")
        self.label.setFont(QFont('Arial', 35))
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(60)
        self.slider.setSingleStep(3)
        self.slider.setValue(10)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(5)

        self.layout.addWidget(self.slider)
        self.slider.valueChanged.connect(self.value_change)

        self.setLayout(self.layout)

    def set_button(self):
        '''Set a capture button on the window.'''
        self.start = QPushButton()
        self.start.setText("Start Capturing")
        self.start.setFont(QFont('Arial', 12))
        self.start.clicked.connect(self.click_start)

        self.exit = QPushButton()
        self.exit.setText("Exit")
        self.exit.setFont(QFont('Arial', 12))
        self.exit.setEnabled(False)
        self.exit.clicked.connect(self.click_exit)

        self.layout.addWidget(self.start)
        self.layout.addWidget(self.exit)
        self.setLayout(self.layout)

    def set_brightness(self, brightness: int):
        '''Adjust the brightness of the screen by sliding the slider.'''
        self.label.setText(f'Brightness: {brightness}')
        sbc.set_brightness(brightness, method=method)

    def value_change(self):
        '''Change the literal value of brightness.'''
        self.set_brightness(self.slider.value())

    pyqtSlot()
    def capture_image(self):
        '''Capture images and adjust the brightness instantly.'''
        cam = cv2.VideoCapture(0)
        while True:
            _, frame = cam.read()
            frame = cv2.flip(frame, flipCode=1) # horizontally flip
            
            # Detect the brightness of the frame and adjust the brightness of the screen.
            brightness = self.detect_brightness(frame)
            self.adjust_brightness(brightness)

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            cv2.imshow('Video Capture', frame)
            cv2.waitKey(50)

            # If exit flag is True, close the webcam and emit the exit signal.
            if self.exit_flag == True:
                self.set_brightness(20)
                cam.release()
                self.s_exit.emit()
                sys.exit(0)

    def get_brightness_percentage(self, frame: np.ndarray):
        """Returns the percentage of brightness mean."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # hue, saturation, value
        # Value is as known as brightness.
        h, s, v = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        # print(f'mean = {v.mean():.2f}({v.mean() / 255:.2%}), std = {v.std():.2f}, var = {v.var():.2f}')

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

    def adjust_brightness(self, brightness: int):
        '''Adjust the brightness of the screen.'''
        self.set_brightness(brightness)

    def click_start(self):
        '''Do things after start button is clicked.'''
        self.slider.hide()
        self.exit.setEnabled(True)
        self.start.setEnabled(False)
        self.capture_image()

    def click_exit(self):
        '''Set exit flag to True.'''
        self.exit_flag = True

    def connect_signal(self):
        '''Connect the exit signal and close the gui.'''
        self.s_exit.connect(self.close)
    

if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = SliderDemo()
    demo.show()
    sys.exit(app.exec_())
