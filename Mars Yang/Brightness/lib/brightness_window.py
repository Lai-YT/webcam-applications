from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from lib.component import Label, CheckBox, HorizontalSlider, Button


class BrightnessGui(QMainWindow):

    def __init__(self, parent=None):
        super().__init__()

        self.setWindowTitle("Auto Brightness Controller")
        self.resize(450, 300)
        self.setWindowIcon(QIcon("sun.ico"))

        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget(parent=self)
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Initialize widgets
        self._set_label()
        self._set_slider()
        self._set_checkbox()
        self._set_buttons()

    def _set_label(self):
        self.label = Label()
        self._general_layout.addWidget(self.label)

    def _set_slider(self):
        self.slider = HorizontalSlider()
        self._general_layout.addWidget(self.slider)

    def _set_checkbox(self):
        self.checkbox = CheckBox("Brightness Optimization")
    
        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.checkbox)
        # Horizontally align center.
        checkbox_layout.setAlignment(Qt.AlignHCenter)
        self._general_layout.addLayout(checkbox_layout)

    def _set_buttons(self):
        self.buttons = {}
        buttons = {"Exit": "Exit"}

        for name, text in buttons.items():
            self.buttons[name] = Button(text)
            self._general_layout.addWidget(self.buttons[name])