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
        self.setWindowTitle("Timer")
        self.setWindowIcon(QIcon(":webcam.ico"))
        self.setFixedSize(500, 350)
        # Set the general layout.
        self._general_layout = QVBoxLayout()
        self.setLayout(self._general_layout)
        # Set break timer.
        self.break_timer = Timer()

        self._set_lcd_timer()
        self._set_break_label()

    def _set_lcd_timer(self):
        '''Set an LCD clock on the window.'''
        time_layout = QFormLayout()
        self.time_label = QLCDNumber()
        self.time_label.display("00:00")
        self.time_label.setDigitCount(5)
        self.time_label.setMinimumHeight(150)

        time_layout.addRow(self.time_label)
        self._general_layout.addLayout(time_layout)

    def _set_break_label(self):
        '''Set message labels to display when break time.'''
        break_layout = QFormLayout()

        self.break_message = Label(font_size=25)
        self.break_message.setAlignment(Qt.AlignCenter)
        self.countdown_message = Label(font_size=25)
        self.countdown_message.setAlignment(Qt.AlignCenter)
        self.encourage_message = Label(font_size=25)
        self.encourage_message.setAlignment(Qt.AlignCenter)
        
        break_layout.addRow(self.break_message)
        break_layout.addRow(self.countdown_message)
        break_layout.addRow(self.encourage_message)
        self._general_layout.addLayout(break_layout)

    def display_time(self, time: float):
        '''Display current time on the clock.'''
        self.time_label.display(f"{(time // 60):02d}:{(time % 60):02d}")

    def break_time_if_too_long(self, timer: Timer, time_limit: int, break_time: int):
        """If the time record in the Timer object exceeds time limit, a break time countdown shows on the timer gui.
        The timer will be paused during the break, reset after the break.

        Arguments:
            timer (Timer): Contains time record
            time_limit (int): Triggers a break if reached (minutes)
            break_time (int): How long the break should be (minutes)
        """
        # minute to second
        time_limit *= 60
        break_time *= 60

        # Break time is over, reset the timer for a new start.
        if self.break_timer.time() > break_time:
            timer.reset()
            self.break_timer.reset()
            self.break_message_clear()
            return

        # not the time to take a break
        if timer.time() < time_limit:
            return

        # Pause the timer and start countdown until break time finish.
        timer.pause()
        self.break_timer.start()
        countdown: int = break_time - self.break_timer.time()
        time_left: str = f"{(countdown // 60):02d}:{(countdown % 60):02d} left."

        # Display break texts on the window when break time.
        break_text = "It's time to take a break!"
        encourage_text = "Coding makes tired."
        self.break_message.setText(break_text)
        self.countdown_message.setText(time_left)
        self.encourage_message.setText(encourage_text)

    def break_message_clear(self):
        '''Clear break messages until next break period.'''
        self.break_message.clear()
        self.countdown_message.clear()
        self.encourage_message.clear()