from PyQt5.QtWidgets import QFormLayout, QWidget

from intergrated_gui.component import Label


class InformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_information()

    def _create_information(self):
        information = {
            "distance": "Face Distance",
            "posture": "Posture Detect:",
            "time": "Focus Time:",
            "concentration": "Concentration Grade:",
            "brightness": "Screen Brightness:",
        }
        self.information = {}

        for name, description in information.items():
            self.information[name] = Label("xxxxxx", font_size=16)
            self._layout.addRow(Label(description, font_size=16), self.information[name])


# class DistanceInformationWidget(QWidget):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#
#         self._layout = QFormLayout()
#         self.setLayout(self._layout)
#
#     def _create_labels(self):
#         self.distance = Label("xxxxxx", font_size=16)
#         self._layout.addRow(Label("Face Distance:", font_size=16), self.distance)
