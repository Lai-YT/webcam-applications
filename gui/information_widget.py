from enum import Enum
from typing import Dict

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFormLayout, QFrame, QWidget

from distance.guard import DistanceState
from gui.component import Label
from gui.popup_widget import TimeState
from posture.calculator import PostureLabel


class TextColor(Enum):
    """If info state has to be warned, set info text in red."""
    BLACK = "black"
    RED = "red"


class InformationWidget(QWidget):
    """Provides update methods to show the results of applications on
    their corresponding labels.
    """
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_information()

    @pyqtSlot(float, DistanceState)
    def update_distance(self, distance: float, state: DistanceState) -> None:
        """Updates distance to the corresponding information label.

        The text color is red if is a warning state; otherwise black.

        Arguments:
            distance: It is rounded to two decimal places.
            state: The state of the distance.
        """
        self.information["distance"].setNum(round(distance, 2))

        color: TextColor = TextColor.BLACK
        if state is DistanceState.WARNING:
            color = TextColor.RED
        self.information["distance"].set_color(color.value)

    @pyqtSlot(int, TimeState)
    def update_time(self, time: int, state: TimeState) -> None:
        """Updates time to the corresponding information label.

        The text color is red if is a break state; otherwise black.

        Arguments:
            time: Time to update, in seconds.
            state: The state of the time.
        """
        time_str = f"{(time // 60):02d}:{(time % 60):02d}"
        self.information["time"].setText(time_str)
        self.information["time-state"].setText(state.name.lower())

        color: TextColor = TextColor.BLACK
        if state is TimeState.BREAK:
            color = TextColor.RED
        self.information["time"].set_color(color.value)
        self.information["time-state"].set_color(color.value)

    @pyqtSlot(PostureLabel, str)
    def update_posture(self, posture: PostureLabel, detail: str) -> None:
        """Updates posture and its detail to the corresponding information label.

        The text color is red if is a slump posture; otherwise black.

        Arguments:
            posture: The label of the posture.
            detail: The extra information to tell about the posture.
        """
        self.information["posture"].setText(posture.name.lower())
        # wraps after colons
        wrapped_detail: str = detail.replace(":", ":\n")
        self.information["posture-detail"].setText(wrapped_detail)

        color: TextColor = TextColor.BLACK
        if posture is PostureLabel.SLUMP:
            color = TextColor.RED
        self.information["posture"].set_color(color.value)
        self.information["posture-detail"].set_color(color.value)

    @pyqtSlot(int)
    def update_brightness(self, brightness: int) -> None:
        self.information["brightness"].setNum(brightness)

    # To show and hide the row of QFormLayout,
    # extra effort is required.
    def hide(self, info: str) -> None:
        """Hides the whole row that contains the field info."""
        row, _ = self._layout.getWidgetPosition(self.information[info])
        self._layout.itemAt(row, QFormLayout.LabelRole).widget().hide()
        self._layout.itemAt(row, QFormLayout.FieldRole).widget().hide()

    def show(self, info: str) -> None:
        """Shows the whole row that contains the field info."""
        row, _ = self._layout.getWidgetPosition(self.information[info])
        self._layout.itemAt(row, QFormLayout.LabelRole).widget().show()
        self._layout.itemAt(row, QFormLayout.FieldRole).widget().show()

    def _create_information(self) -> None:
        """Creates the labels for information."""

        information: Dict[str, str] = {
            "distance": "Face Distance:",
            "posture": "Posture Detect:",
            "posture-detail": "Detail:",
            "time": "Focus Time:",
            "time-state": "Timer State:",
            "brightness": "Screen Brightness:",
        }
        self.information: Dict[str, Label] = {}

        font_size: int = 15
        for name, description in information.items():
            # Notice that if the line wrap isn't set to True,
            # the label might grow and affect size of other widget.
            self.information[name] = Label(font_size=font_size, wrap=True)
            self.information[name].setFrameStyle(QFrame.WinPanel | QFrame.Raised)
            self._layout.addRow(Label(description, font_size=font_size), self.information[name])
