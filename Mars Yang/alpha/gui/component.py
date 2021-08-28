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


class MessageLabel(QLabel):
    """MessageLabel is used to display warnings or errors."""
    def __init__(self, text="", font_size=10, color="red"):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
        self.setStyleSheet(f"color: {color};")
        self.setWordWrap(True)


class LineEdit(QLineEdit):
    def __init__(self, text="", font_size=12):
        super().__init__(text)
        self.setPlaceholderText(text)
        self.setFont(QFont("Arial", font_size))

    def set_placeholder_text(self, text, font_size=12):
        super().setPlaceholderText(text)
        self.setFont(QFont("Arial", font_size))


class ActionButton(QPushButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
