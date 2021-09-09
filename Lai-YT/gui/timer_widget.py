from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLCDNumber, QStackedLayout, QVBoxLayout, QWidget

from gui.component import Label


class TimerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set some main window's properties.
        self.setWindowTitle("Timer")
        self.setWindowIcon(QIcon(":webcam.ico"))
        self.setFixedSize(250, 150)
        # Set the general layout.
        self._general_layout = QStackedLayout()
        self.setLayout(self._general_layout)

        self._create_lcd_timer()
        self._create_break_messages()

    def switch_time_mode(self, mode: str):
        if mode == "break":
            self._general_layout.setCurrentWidget(self.break_time)
        elif mode == "work":
            self._general_layout.setCurrentWidget(self.work_time)
        else:
            raise

    def _create_lcd_timer(self):
        self.work_time = QLCDNumber()
        self._general_layout.addWidget(self.work_time)

    def _create_break_messages(self):
        self.break_time = QWidget()
        break_layout = QVBoxLayout()
        self.messages = {}
        messages = {
            "Break": "It's time to take a break!",
            "Countdown": "",
            "Encourage": "Coding makes tired.",
        }
        for name, msg in messages.items():
            self.messages[name] = Label(msg)
            self.messages[name].setAlignment(Qt.AlignCenter)
            break_layout.addWidget(self.messages[name])

        self.break_time.setLayout(break_layout)
        self._general_layout.addWidget(self.break_time)
