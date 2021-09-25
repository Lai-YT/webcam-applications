from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QLabel, QCheckBox, QSlider, QPushButton


"""Initialize basic structures of all widget used in this gui."""
class Label(QLabel):
    def __init__(self, text="", font_size=35, wrap=False):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
        # Align center
        self.setAlignment(Qt.AlignCenter)
        self.setWordWrap(wrap)

class CheckBox(QCheckBox):
    def __init__(self, text, font_size=14):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))

class HorizontalSlider(QSlider):
    def __init__(self, min_val=0, max_val=12, cur_val=6):
        super().__init__(Qt.Horizontal)
        self.setRange(min_val, max_val)
        self.setValue(cur_val)
        # Set the scale below the slider.
        self.setTickPosition(QSlider.TicksBelow)

class Button(QPushButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))