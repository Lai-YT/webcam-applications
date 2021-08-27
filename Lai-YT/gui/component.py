from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QCheckBox
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QLineEdit
from PyQt5.QtWidgets import QPushButton


class OptionCheckBox(QCheckBox):
    def __init__(self, text="", font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class Label(QLabel):
    def __init__(self, text="", font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class LineEdit(QLineEdit):
    def __init__(self, text="", font_size=12):
        super().__init__()
        self.setPlaceholderText(text)
        self.setFont(QFont("Arial", font_size))


class ActionButton(QPushButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
