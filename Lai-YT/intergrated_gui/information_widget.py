from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFormLayout, QWidget

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
        self.information["distance"].setText(f"{distance:.02f}")

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
            self._layout.addRow(Label(description, font_size=font_size), self.information[name])
