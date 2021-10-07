from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QFormLayout, QVBoxLayout, QWidget

from intergrated_gui.component import CheckableGroupBox, Label, LineEdit, OptionRadioButton


class PanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        groups = {
            "distance": DistanceGroupBox(),
            "time": TimeGroupBox(),
            "posture": PostureGroupBox(),
            "brightness": BrightnessGroupBox(),
        }

        layout = QVBoxLayout()
        for name, group in groups.items():
            layout.addWidget(group, stretch=1)
        layout.addStretch(5)
        self.setLayout(layout)


class DistanceGroupBox(CheckableGroupBox):
    def __init__(self, parent=None):
        super().__init__("Distance Measurement", parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_settings()
        self._set_restrictions()

    def _create_settings(self):
        settings = {
            "width": "Face width:",
            "distance": "Distance in reference:",
            "bound": "Shortest distance allowed:",
        }
        self.settings = {}
        for name, description in settings.items():
            self.settings[name] = LineEdit()
            self._layout.addRow(description, self.settings[name])

        # sound warning is enabled in default
        self.warning = OptionRadioButton("enable sound warning")
        self.warning.setChecked(True)
        self._layout.addRow(self.warning)

    def _set_restrictions(self):
        # placeholder, double validator, max length
        restrictions = {
            "width": ("5 ~ 24.99 (cm)", (5, 24.99, 2), 5),
            "distance": ("10 ~ 99.99 (cm)", (10, 99.99, 2), 5),
            "bound": ("30 ~ 59.99 (cm)", (30, 59.99, 2), 5),
        }

        for name, (placeholder, validator, length) in restrictions.items():
            self.settings[name].setPlaceholderText(placeholder)
            self.settings[name].setValidator(QDoubleValidator(*validator))
            self.settings[name].setMaxLength(length)


class TimeGroupBox(CheckableGroupBox):
    def __init__(self, parent=None):
        super().__init__("Focus Timing", parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_settings()
        self._set_restrictions()

    def _create_settings(self):
        settings = {
            "limit": "Time limit:",
            "break": "Break time:",
        }
        self.settings = {}
        for name, description in settings.items():
            self.settings[name] = LineEdit()
            self._layout.addRow(description, self.settings[name])

        # sound warning is enabled in default
        self.warning = OptionRadioButton("enable sound warning")
        self.warning.setChecked(True)
        self._layout.addRow(self.warning)

    def _set_restrictions(self):
        # placeholder, validator
        restrictions = {
            "limit": ("1 ~ 59 (min)", (1, 59)),
            "break": ("1 ~ 59 (min)", (1, 59)),
        }

        for name, (placeholder, validator) in restrictions.items():
            self.settings[name].setPlaceholderText(placeholder)
            self.settings[name].setValidator(QIntValidator(*validator))


class PostureGroupBox(CheckableGroupBox):
    def __init__(self, parent=None):
        super().__init__("Posture Detection", parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_settings()
        self._set_restrictions()

    def _create_settings(self):
        settings = {
            "angle": "Allowed slope angle:",
        }
        self.settings = {}
        for name, description in settings.items():
            self.settings[name] = LineEdit()
            self._layout.addRow(description, self.settings[name])

        self.custom = OptionRadioButton("use customized model")
        self._layout.addRow(self.custom)

    def _set_restrictions(self):
        # placeholder, double validator, max length
        restrictions = {
            "angle": ("5 ~ 24.99 (deg)", (5, 24.99, 2), 5),
        }

        for name, (placeholder, validator, length) in restrictions.items():
            self.settings[name].setPlaceholderText(placeholder)
            self.settings[name].setValidator(QDoubleValidator(*validator))
            self.settings[name].setMaxLength(length)


class BrightnessGroupBox(CheckableGroupBox):
    def __init__(self, parent=None):
        super().__init__("Brightness Optimization", parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_modes()

    def _create_modes(self):
        # name | description
        modes = {
            "webcam": "Webcam-based brightness detector \n(webcam required)",
            "color-system": "Color-system mode",
        }
        self.modes = {}
        for mode, description in modes.items():
            self.modes[mode] = OptionRadioButton(description)
            self._layout.addWidget(self.modes[mode])

        # default mode
        self.modes["webcam"].setChecked(True)
