from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QLCDNumber, QStackedLayout, QVBoxLayout, QWidget

import gui.img.icon
from gui.component import Label


class TimerWidget(QWidget):
    """TimerWidget contains different time states maintain by a QStackedLayout."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set some basic properties.
        self.setWindowTitle("Timer")
        self.setWindowIcon(QIcon(":webcam.ico"))
        self.setFixedSize(250, 150)
        # A stacked layout is used to have multiple time states switching
        # on the same area.
        self._general_layout = QStackedLayout()
        self.setLayout(self._general_layout)

        self._states = {}
        self._create_lcd_timer()
        self._create_break_messages()
        # Work state is the initial state.
        self.switch_time_state("work")

    def current_state(self):
        """Returns the current state of the TimerWidget."""
        return self._current_state

    def switch_time_state(self, state: str):
        """
        Arguments:
            state ("work" | "break")
        """
        try:
            self._general_layout.setCurrentWidget(self._states[state])
        except KeyError:
            raise ValueError(f'Valid states are ("work" | "break") but "{state}" is passed') from None

        self._current_state = state

    def _create_lcd_timer(self):
        self.work_time = QLCDNumber()
        self._general_layout.addWidget(self.work_time)
        # LCD number should be shown under work state.
        self._states["work"] = self.work_time

    def _create_break_messages(self):
        break_layout = QVBoxLayout()
        self.messages = {}
        # There are 3 labels of messages, 2 of them are fixed.
        messages = {
            "Break": "It's time to take a break!",
            "Countdown": "",
            "Encourage": "Coding makes tired.",
        }
        for name, msg in messages.items():
            self.messages[name] = Label(msg, font_size=14)
            self.messages[name].setAlignment(Qt.AlignCenter)
            break_layout.addWidget(self.messages[name])

        self.break_time = QWidget()
        self.break_time.setLayout(break_layout)
        self._general_layout.addWidget(self.break_time)
        # Break time messages should be shown under break state.
        self._states["break"] = self.break_time
