from PyQt5.QtWidgets import QFormLayout, QWidget

from intergrated_gui.component import Label


class InformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)
        self.setStyleSheet("border: 1px solid black;")

        self._create_information()

    def update_distance(self, distance: float) -> None:
        self.information["distance"].setText(f"{distance:.02f}")

    def update_posture(self, posture, explanation):
        self.information["posture"].setText(posture.name)
        self.information["posture-explanation"].setText(explanation)

    def _create_information(self):
        information = {
            "distance": "Face Distance:",
            "posture": "Posture Detect:",
            "posture-explanation": "Explanation:",
            "time": "Focus Time:",
            "concentration": "Concentration Grade:",
            "brightness": "Screen Brightness:",
        }
        self.information = {}

        font_size=16
        for name, description in information.items():
            self.information[name] = Label(font_size=font_size, wrap=True)
            self._layout.addRow(Label(description, font_size=font_size), self.information[name])
