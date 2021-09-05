from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QCheckBox, QLabel, QLineEdit, QPushButton


class OptionCheckBox(QCheckBox):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class Label(QLabel):
    def __init__(self, text="", font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class MessageLabel(QLabel):
    """MessageLabel is used to display warning or status.
    Also provides simple color setting method.
    """
    def __init__(self, text="", font_size=10, color="red"):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
        self.set_color(color)
        self.setWordWrap(True)

    def set_color(self, color):
        self.setStyleSheet(f"color: {color};")


class LineEdit(QLineEdit):
    """Placeholder text is easily set with constructor.
    Also provides simple color setting method.
    """
    def __init__(self, text="", font_size=12):
        super().__init__(text)
        self.setPlaceholderText(text)
        self.setFont(QFont("Arial", font_size))

    def set_color(self, color):
        self.setStyleSheet(f"color: {color};")


class ActionButton(QPushButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
