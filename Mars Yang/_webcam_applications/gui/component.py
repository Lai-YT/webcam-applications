from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QCheckBox, QLabel, QLineEdit, QProgressBar,
                             QPushButton, QRadioButton, QStatusBar)


class OptionCheckBox(QCheckBox):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class Label(QLabel):
    def __init__(self, text="", font_size=12, wrap=False):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
        self.setWordWrap(wrap)


class MessageLabel(Label):
    """MessageLabel is used to display warning or status.
    Also provides simple color setting method.
    """
    def __init__(self, text="", font_size=10, color="red"):
        super().__init__(text, font_size)
        self.set_color(color)

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


class StatusBar(QStatusBar):
    def __init__(self, font_size=12):
        super().__init__()
        self.setFont(QFont("Arial", font_size))
        self.setStyleSheet(f"color: gray;")
        self.setSizeGripEnabled(False)

    def remove_widget(self, widget):
        """Deletes the widget from status bar.
        The original removeWidget() method hides but not deletes the widegt.
        """
        super().removeWidget(widget)
        widget.deleteLater()


class LoadingBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setRange(0, 0)


class OptionRadioButton(QRadioButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
