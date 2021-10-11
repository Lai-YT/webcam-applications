from PyQt5.QtWidgets import QFormLayout, QVBoxLayout, QWidget

from intergrated_gui.component import Label


class InformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_information()

    def update_distance(self, distance: float) -> None:
        self.information["distance"].update_distance(distance)

    def _create_information(self):
        self.information = {
            "distance": DistanceInformationWidget(),
            "posture": PostureInformationWidget(),
            "time": TimeInformationWidget(),
            "concentration": ConcentrationInformationWidget(),
            "brightness": BrightnessInformationWidget(),
        }

        for widget in self.information.values():
            self._layout.addWidget(widget, stretch=1)

        self._layout.addStretch(5)


class DistanceInformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_labels()

    def _create_labels(self):
        self.distance = Label(font_size=16)
        self._layout.addRow(Label("Face Distance:", font_size=16), self.distance)

    def update_distance(self, distance: float) -> None:
        self.distance.setText(f"{distance:.02f}")


class PostureInformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_labels()

    def _create_labels(self):
        self.posture = Label(font_size=16)
        self._layout.addRow(Label("Posture Detect:", font_size=16), self.posture)


class TimeInformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_labels()

    def _create_labels(self):
        self.time = Label(font_size=16)
        self._layout.addRow(Label("Focus Time:", font_size=16), self.time)


class ConcentrationInformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_labels()

    def _create_labels(self):
        self.concentration = Label(font_size=16)
        self._layout.addRow(Label("Concentration Grade:", font_size=16), self.concentration)


class BrightnessInformationWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_labels()

    def _create_labels(self):
        self.brightness = Label(font_size=16)
        self._layout.addRow(Label("Screen Brightness:", font_size=16), self.brightness)
