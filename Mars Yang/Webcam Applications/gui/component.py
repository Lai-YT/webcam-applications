from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QCheckBox, QLCDNumber, QLabel, QLineEdit, QMessageBox,
                             QProgressBar, QProgressDialog, QPushButton, QRadioButton,
                             QStatusBar)


class ActionButton(QPushButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class CaptureMessageBox(QMessageBox):
    def __init__(self, label, number_of_images, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Finish")
        self.setIcon(QMessageBox.Information)
        self.setText(f"You've captured {number_of_images} images of label '{label.name}.'")
        self.setFont(QFont("Arial", 12))


class LCDClock(QLCDNumber):
    def __init__(self, color="black"):
        super().__init__()
        self.display("00:00")
        self.setStyleSheet(f"color: {color};")


class Label(QLabel):
    def __init__(self, text="", font_size=12, wrap=False):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))
        self.setWordWrap(wrap)


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


class LoadingBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setRange(0, 0)


class MessageLabel(Label):
    """MessageLabel is used to display warning or status.
    Also provides simple color setting method.
    """
    def __init__(self, text="", font_size=10, color="red"):
        super().__init__(text, font_size)
        self.set_color(color)

    def set_color(self, color):
        self.setStyleSheet(f"color: {color};")


class OptionCheckBox(QCheckBox):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class OptionRadioButton(QRadioButton):
    def __init__(self, text, font_size=12):
        super().__init__(text)
        self.setFont(QFont("Arial", font_size))


class ProgressDialog(QProgressDialog):
    def __init__(self, maximum, parent=None):
        super().__init__(parent)
        # Block input to other windows.
        self.setModal(True)
        # Don't need a cancel button.
        # (May add it to let the user quit training.)
        self.setCancelButton(None)
        self.setMaximum(maximum)
        self.setFixedSize(300, 100)
        self.setFont(QFont("Arial", 16))

        self._set_label()

    def _set_label(self):
        label = Label(font_size=14)
        label.setAlignment(Qt.AlignCenter)
        self.setLabel(label)


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


class FailMessageBox(QMessageBox):
    """The is a message box that shows an error (failed progress)."""
    
    def __init__(self, fail_message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fail")
        self.setIcon(QMessageBox.Critical)
        self.setText(fail_message)
        self.setFont(QFont("Arial", 12))
