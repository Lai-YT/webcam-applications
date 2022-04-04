"""PyQt5.QtWidgets with common-use settings.

All with font "Arial".
"""
from typing import List
from PyQt5.QtGui import QFont
from PyQt5 import QtWidgets


class _ArialFont(QFont):
    """A QFont class with the first argument of constructor be "Arial"."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__("Arial", *args, **kwargs)


class ActionButton(QtWidgets.QPushButton):
    def __init__(self, text: str, font_size: int = 12) -> None:
        super().__init__(text)
        self.setFont(_ArialFont(font_size))

class PullDownMenu(QtWidgets.QComboBox):
    def __init__(self, font_size: int = 16) -> None:
        super().__init__()
        self.setFixedSize(120, 40)
        self.setFont(_ArialFont(font_size))

    def add_item(self, item: str) -> None:
        self.addItem(item)

class Label(QtWidgets.QLabel):
    def __init__(self, text: str = "",
                 font_size: int = 25, wrap: bool = False) -> None:
        super().__init__(text)
        self.setFont(_ArialFont(font_size))
        self.setWordWrap(wrap)

    def set_color(self, color: str) -> None:
        """Sets the text color of the label."""
        self.setStyleSheet(f"color: {color};")

class LineEdit(QtWidgets.QLineEdit):
    """Placeholder text is easily set with constructor.
    Also provides simple color setting method.
    """
    def __init__(self, place_hold_text: str = "", font_size: int = 20) -> None:
        super().__init__()
        self.setPlaceholderText(place_hold_text)
        self.setFixedWidth(450)
        self.setFont(_ArialFont(font_size))

    def set_color(self, color: str) -> None:
        """Sets the text color of the line."""
        self.setStyleSheet(f"color: {color};")
