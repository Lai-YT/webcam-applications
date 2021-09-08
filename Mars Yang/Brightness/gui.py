import sys
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

import cv2
import screen_brightness_control as sbc


class SliderDemo(QDialog):
    def __init__(self, parent=None):
        super(SliderDemo, self).__init__(parent)

        self.setWindowTitle("= =")
        self.resize(1000, 400)

        self.layout = QVBoxLayout()
        self.setSlider()
        self.setBrightness()

    def setSlider(self):
        self.label = QLabel("I want to go to sleep.")
        self.label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(10)
        self.slider.setMaximum(80)
        self.slider.setSingleStep(3)
        self.slider.setValue(20)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(5)

        self.layout.addWidget(self.slider)

        self.slider.valueChanged.connect(self.valueChange)

        self.setLayout(self.layout)

    def setBrightness(self, brightness=20):
        method = 'wmi'
        sbc.set_brightness(brightness, method=method)

    def valueChange(self):
        self.label.setText(f'Brightness: {self.slider.value()}')
        size = self.slider.value()
        self.label.setFont(QFont('Arial', size))
        self.setBrightness(brightness=size)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    demo = SliderDemo()
    demo.show()
    sys.exit(app.exec_())
