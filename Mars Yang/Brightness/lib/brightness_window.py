import screen_brightness_control as sbc

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

method = 'wmi'

class BrightnessGui(QMainWindow):

    def __init__(self, parent=None):
        super(BrightnessGui, self).__init__(parent)

        self.setWindowTitle("Brightness Detector")
        self.resize(450, 300)
        self.setWindowIcon(QIcon("sun.ico"))
        self.layout = QVBoxLayout()
        self.set_slider()
        self.set_button()
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

        self.setLayout(self.layout)

    def set_button(self):
        '''Set a capture button on the window.'''
        self.start = QPushButton()
        self.start.setText("Start Capturing")
        self.start.setFont(QFont('Arial', 12))
    
        self.exit = QPushButton()
        self.exit.setText("Exit")
        self.exit.setFont(QFont('Arial', 12))
        self.exit.setEnabled(False)

        self.layout.addWidget(self.start)
        self.layout.addWidget(self.exit)
        self.setLayout(self.layout)