from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget)

from lib.component import (Label, CheckBox, HorizontalSlider, Button)

class BrightnessGui(QMainWindow):

    def __init__(self, parent=None):
        super(BrightnessGui, self).__init__(parent)

        self.setWindowTitle("Auto Brightness Controller")
        self.resize(450, 300)
        self.setWindowIcon(QIcon("sun.ico"))

        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget(parent=self)
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Initialize widgets
        self.set_label()
        self.set_checkbox()
        self.set_slider()
        self.set_buttons()
        # Initialize exit flag.
        self.exit_flag = False

    def set_label(self):
        self.label = Label()
        self._general_layout.addWidget(self.label)

    def set_checkbox(self):
        self.lock = CheckBox("Lock Brightness")
        self.lock.hide()
        self._general_layout.addWidget(self.lock)

    def set_slider(self):
        self.slider = HorizontalSlider()
        self._general_layout.addWidget(self.slider)

    def set_buttons(self):
        self.buttons = {}
        buttons = {
            "Start": "Start Capturing",
            "Exit": "Exit"
        }

        for name, label in buttons.items():
            self.buttons[name] = Button(label)
            self._general_layout.addWidget(self.buttons[name])

        self.buttons["Exit"].setEnabled(False)