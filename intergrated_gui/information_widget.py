from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFormLayout, QFrame, QWidget

from intergrated_gui.component import Label
from lib.train import PostureLabel


class InformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_information()

    @pyqtSlot(float)
    def update_distance(self, distance: float) -> None:
        """Updates distance to the corresponding information label.

        Arguments:
            distance (float): It is rounded to two decimal places
        """
        self.information["distance"].setNum(round(distance, 2))

    @pyqtSlot(int, str)
    def update_time(self, time: int, state: str) -> None:
        """
        Arguments:
            time (int): Time to update, in seconds
            state (str): The state of the time to display
        """
        time_str = f"{(time // 60):02d}:{(time % 60):02d}"
        self.information["time"].setText(time_str)
        self.information["time-state"].setText(state)

    @pyqtSlot(PostureLabel, str)
    def update_posture(self, posture: PostureLabel, explanation: str) -> None:
        self.information["posture"].setText(posture.name)
        self.information["posture-explanation"].setText(explanation)

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

    def _create_information(self):
        information = {
            "distance": "Face Distance:",
            "posture": "Posture Detect:",
            "posture-explanation": "Explanation:",
            "time": "Focus Time:",
            "time-state": "Timer State:",
            "concentration": "Concentration Grade:",
            "brightness": "Screen Brightness:",
        }
        self.information = {}

        font_size=16
        for name, description in information.items():
            # Notice that if the line warp isn't set to True,
            # the label might grow and affect size of other widget.
            self.information[name] = Label(font_size=font_size, wrap=True)
            self.information[name].setFrameStyle(QFrame.WinPanel | QFrame.Raised)
            self._layout.addRow(Label(description, font_size=font_size), self.information[name])
