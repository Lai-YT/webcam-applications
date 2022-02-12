"""PyQt5.QtWidgets with common-use settings.

All with font "Arial".
"""

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5 import QtWidgets

from posture.train import PostureLabel


class _ArialFont(QFont):
    """A QFont class with the first argument of constructor be "Arial"."""
    def __init__(self, *args, **kwargs) -> None:
        super().__init__("Arial", *args, **kwargs)


class ActionButton(QtWidgets.QPushButton):
    def __init__(self, text: str, font_size: int = 12) -> None:
        super().__init__(text)
        self.setFont(_ArialFont(font_size))


class CaptureMessageBox(QtWidgets.QMessageBox):
    """Displays the result of capturing the image of posture model."""
    def __init__(
            self,
            label: PostureLabel,
            number_of_images: int,
            parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Finish")
        self.setIcon(QtWidgets.QMessageBox.Information)
        self.setText(f"You've captured {number_of_images} images of label '{label.name}.'")
        self.setFont(_ArialFont(12))


class CheckableGroupBox(QtWidgets.QGroupBox):
    def __init__(self, title: str, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(False)
        self.setFont(_ArialFont(12))


class HorizontalSlider(QtWidgets.QSlider):
    def __init__(self,
                 min_val: int = 0,
                 max_val: int = 100, cur_val: int = 30) -> None:
        super().__init__(Qt.Horizontal)
        self.setRange(min_val, max_val)
        self.setValue(cur_val)


class LCDClock(QtWidgets.QLCDNumber):
    def __init__(self, color: str = "black") -> None:
        super().__init__()
        self.display("00:00")
        self.setStyleSheet(f"color: {color};")


class Label(QtWidgets.QLabel):
    def __init__(self, text: str = "",
                 font_size: int = 12, wrap: bool = False) -> None:
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
    def __init__(self, place_hold_text: str = "", font_size: int = 12) -> None:
        super().__init__()
        self.setPlaceholderText(place_hold_text)
        self.setFont(_ArialFont(font_size))

    def set_color(self, color: str) -> None:
        """Sets the text color of the line."""
        self.setStyleSheet(f"color: {color};")


class LoadingBar(QtWidgets.QProgressBar):
    """The min and max range are both set to 0 to provide a loading effect."""
    def __init__(self) -> None:
        super().__init__()
        self.setRange(0, 0)


class MessageLabel(Label):
    """MessageLabel is used to display warning or status.
    Also provides simple color setting method.
    """
    def __init__(self, text: str = "",
                 font_size: int = 10, color: str = "red") -> None:
        super().__init__(text, font_size)
        self.set_color(color)

    def set_color(self, color: str) -> None:
        """Sets the color of the message text."""
        self.setStyleSheet(f"color: {color};")


class OptionCheckBox(QtWidgets.QCheckBox):
    def __init__(self, text: str, font_size: int = 12) -> None:
        super().__init__(text)
        self.setFont(_ArialFont(font_size))


class OptionRadioButton(QtWidgets.QRadioButton):
    def __init__(self, text: str, font_size: int = 12) -> None:
        super().__init__(text)
        self.setFont(_ArialFont(font_size))


class ProgressDialog(QtWidgets.QProgressDialog):
    """A modal to show the progress."""
    def __init__(self, maximum: int, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        # Block input to other windows.
        self.setModal(True)
        # Don't need a cancel button.
        # (May add it to let the user quit training.)
        self.setCancelButton(None)
        self.setMaximum(maximum)
        self.setFixedSize(300, 100)
        self.setFont(_ArialFont(16))

        self._set_label()

    def _set_label(self) -> None:
        label = Label(font_size=14)
        label.setAlignment(Qt.AlignCenter)
        self.setLabel(label)


class StatusBar(QtWidgets.QStatusBar):
    def __init__(self, font_size: int = 12) -> None:
        super().__init__()
        self.setFont(_ArialFont(font_size))
        self.setStyleSheet(f"color: gray;")
        self.setSizeGripEnabled(False)

    def remove_widget(self, widget: QtWidgets.QWidget) -> None:
        """Deletes the widget from status bar.
        The original removeWidget() method hides but not deletes the widegt.
        """
        super().removeWidget(widget)
        widget.deleteLater()


class FailMessageBox(QtWidgets.QMessageBox):
    """The is a critical message box that shows an error (failed progress)."""
    def __init__(self, fail_message: str,
                 parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fail")
        self.setIcon(QtWidgets.QMessageBox.Critical)
        self.setText(fail_message)
        self.setFont(_ArialFont(12))
