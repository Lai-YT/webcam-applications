"""PyQt5.QtWidgets with common-use settings.

All with font "Arial".
"""
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

class Label(QtWidgets.QLabel):
    def __init__(self, text: str = "",
                 font_size: int = 25, wrap: bool = False) -> None:
        super().__init__(text)
        self.setFont(_ArialFont(font_size))
        self.setWordWrap(wrap)

    def set_color(self, color: str) -> None:
        """Sets the text color of the label."""
        self.setStyleSheet(f"color: {color};")
