from enum import IntEnum

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QFormLayout, QGridLayout, QGroupBox, QVBoxLayout, QWidget

from intergrated_gui.component import (CheckableGroupBox, HorizontalSlider, Label, LineEdit, OptionCheckBox,
                                       OptionRadioButton)


class PanelWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.panels = {
            "distance": DistancePanel(),
            "time": TimePanel(),
            "posture": PosturePanel(),
            "brightness": BrightnessPanel(),
        }

        layout = QVBoxLayout()
        for name, panel in self.panels.items():
            layout.addWidget(panel, stretch=1)
        layout.addStretch(5)
        self.setLayout(layout)


class DistancePanel(CheckableGroupBox):
    def __init__(self, parent=None):
        super().__init__("Distance Measurement", parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_settings()
        self._set_restrictions()

    def _create_settings(self):
        settings = {
            "distance": "Distance in reference:",
            "bound": "Shortest distance allowed:",
        }
        self.settings = {}
        for name, description in settings.items():
            self.settings[name] = LineEdit()
            self._layout.addRow(description, self.settings[name])

        # sound warning is enabled in default
        self.warning = OptionCheckBox("enable sound warning")
        self.warning.setChecked(True)
        self._layout.addRow(self.warning)

    def _set_restrictions(self):
        # placeholder, double validator, max length
        restrictions = {
            "distance": ("10 ~ 99.99 (cm)", (10, 99.99, 2), 5),
            "bound": ("30 ~ 59.99 (cm)", (30, 59.99, 2), 5),
        }

        for name, (placeholder, validator, length) in restrictions.items():
            self.settings[name].setPlaceholderText(placeholder)
            self.settings[name].setValidator(QDoubleValidator(*validator))
            self.settings[name].setMaxLength(length)


class TimePanel(CheckableGroupBox):
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
        self.warning = OptionCheckBox("enable sound warning")
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


class AngleTolerance(IntEnum):
    """An IntEnum used to represent the angle options of PosturePanel.
    The int value is the angle allowed.
    """
    # Add member or modify value to provide more choices.
    LOOSE = 25
    STRICT = 15

class PosturePanel(CheckableGroupBox):
    def __init__(self, parent=None):
        super().__init__("Posture Detection", parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_settings()

    def _create_settings(self):
        group_box = QGroupBox("Allowed slope angle:")
        box_layout = QVBoxLayout()
        group_box.setLayout(box_layout)
        self._layout.addWidget(group_box)

        angles = [AngleTolerance.LOOSE, AngleTolerance.STRICT]
        self.angles = {}
        for tolerance in angles:
            self.angles[tolerance] = OptionRadioButton(f"{tolerance.name.lower()} ({tolerance} degrees)")
        # a loose angle tolerance is used in default
        self.angles[AngleTolerance.LOOSE].setChecked(True)

        for btn in self.angles.values():
            box_layout.addWidget(btn)

        # sound warning is enabled in default
        self.warning = OptionCheckBox("enable sound warning")
        self.warning.setChecked(True)
        self._layout.addWidget(self.warning)

        self.custom = OptionCheckBox("use customized model")
        self._layout.addWidget(self.custom)


class BrightnessPanel(CheckableGroupBox):
    def __init__(self, parent=None):
        super().__init__("Brightness Optimization", parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_slider()
        self._create_modes()

    def _create_slider(self):
        self.slider = HorizontalSlider()
        self._min_value_label = Label("0", font_size=10)
        self._max_value_label = Label("100", font_size=10)

        slider_layout = QGridLayout()
        slider_layout.addWidget(self.slider, 0, 0)
        slider_layout.addWidget(self._min_value_label, 1, 0)
        slider_layout.addWidget(self._max_value_label, 1, 1)

        self._layout.addLayout(slider_layout)

    def _create_modes(self):
        # name | description
        modes = {
            "webcam": "Webcam-based brightness detector \n(webcam required)",
            "color-system": "Color-system mode",
        }
        self.modes = {}
        for mode, description in modes.items():
            self.modes[mode] = OptionRadioButton(description)
            self.modes[mode].setAutoExclusive(False)
            self._layout.addWidget(self.modes[mode])

        # default mode
        self.modes["webcam"].setChecked(True)

        # sound warning is enabled in default
        self.warning = OptionCheckBox("enable sound warning")
        self.warning.setChecked(True)
        self._layout.addWidget(self.warning)
