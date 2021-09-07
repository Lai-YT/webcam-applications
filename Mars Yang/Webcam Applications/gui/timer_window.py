from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QVBoxLayout, QFormLayout, QDialog, QLCDNumber

from gui.component import Label
from lib.timer import Timer

# No pain, no gain.

class TimerGui(QDialog):

    def __init__(self):
        super().__init__()
        # Set some main window's properties.
        self.setWindowTitle("Break Time!!")
        self.setWindowIcon(QIcon(":webcam.ico"))
        self.setFixedSize(500, 250)
        # Set the general layout.
        self._general_layout = QVBoxLayout()
        self.setLayout(self._general_layout)

        self._set_time_label()

    def _set_time_label(self):
        time_layout = QFormLayout()
        self.time_label = QLCDNumber()
        self.time_label.display("00:00")
        self.time_label.setDigitCount(5)
        self.time_label.setMinimumHeight(200)

        time_layout.addRow(self.time_label)
        self._general_layout.addLayout(time_layout)

    def display_time(self, time: float):
        self.time_label.display(f"{(time // 60):02d}:{(time % 60):02d}")

    def display_break(self):
        break_layout = QFormLayout()
        break_text = "It's time to take a break!"
        encourage_text = "To rest is to prepare for a longer journey ahead."
        self.break_message = Label(text=break_text, font_size=25)
        self.break_message.setAlignment(Qt.AlignCenter)
        self.countdown_message = Label(font_size=25)
        self.countdown_message.setAlignment(Qt.AlignCenter)
        self.encourage_message = Label(text=encourage_text, font_size=14)
        self.encourage_message.setAlignment(Qt.AlignCenter)
        
        break_layout.addRow(self.break_message)
        break_layout.addRow(self.countdown_message)
        break_layout.addRow(self.encourage_message)
        self._general_layout.addLayout(break_layout)

    def break_message_clear(self):
        self.break_message.clear()
        self.countdown_message.clear()
        self.encourage_message.clear()