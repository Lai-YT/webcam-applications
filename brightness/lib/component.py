"""Initialize basic structures of all widget used in this gui."""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QCheckBox, QLabel, QMessageBox, QPushButton, QSlider,
                             QRadioButton)


class Button(QPushButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class CheckBox(QCheckBox):
    def __init__(self, text, font_size=14):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class FailMessageBox(QMessageBox):
    """The is a message box that shows an error (failed progress)."""
    def __init__(self, fail_message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fail")
        self.setIcon(QMessageBox.Critical)
        self.setText(fail_message)
        self.setFont(QFont("Arial", 12))


class HorizontalSlider(QSlider):
    def __init__(self, min_val=0, max_val=100, cur_val=30):
        super().__init__(Qt.Horizontal)
        self.setRange(min_val, max_val)
        self.setValue(cur_val)
        # Set the scale below the slider.
        self.setTickPosition(QSlider.TicksBelow)
        self.setTickInterval(10)


class Label(QLabel):
    def __init__(self, text="", font_size=35, wrap=False):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
        # Align center
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(wrap)


class DontShowAgainWarningMessage(QMessageBox):
    """This is a warning message box with don't show again checkbox."""
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Warning")
        self.setIcon(QMessageBox.Warning)
        self.setText(text)
        self.setFont(QFont("Arial", 12))
        self._create_dont_show_again_checkbox()

    def _create_dont_show_again_checkbox(self):
        self.dont_show_again_checkbox = CheckBox("Don't show again.", font_size=12)
        self.setCheckBox(self.dont_show_again_checkbox)


class OptionRadioButton(QRadioButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
