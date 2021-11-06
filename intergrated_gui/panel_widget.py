from enum import IntEnum
from typing import Dict

from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import QFormLayout, QGridLayout, QGroupBox, QVBoxLayout, QWidget

from intergrated_gui.component import (CheckableGroupBox, HorizontalSlider, Label,
                                       LineEdit, OptionCheckBox, OptionRadioButton)
from lib.brightness_calcuator import BrightnessMode


class PanelWidget(QWidget):
    def __init__(self, parent: QWidget= None) -> None:
        super().__init__(parent)

        self.panels: Dict[str, CheckableGroupBox] = {
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
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Distance Measurement", parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_settings()
        self._set_restrictions()

    def _create_settings(self) -> None:
        settings = {
            "camera_dist": "Distance in reference:",
            "warn_dist": "Shortest distance allowed:",
        }
        self.settings: Dict[str, LineEdit] = {}
        for name, description in settings.items():
            self.settings[name] = LineEdit()
            self._layout.addRow(description, self.settings[name])

        # sound warning is enabled in default
        self.warning = OptionCheckBox("enable sound warning")
        self.warning.setChecked(True)
        self._layout.addRow(self.warning)

    def _set_restrictions(self) -> None:
        # placeholder, double validator, max length
        restrictions = {
            "camera_dist": ("10 ~ 99.99 (cm)", (10, 99.99, 2), 5),
            "warn_dist": ("30 ~ 59.99 (cm)", (30, 59.99, 2), 5),
        }

        for name, (placeholder, validator, length) in restrictions.items():
            self.settings[name].setPlaceholderText(placeholder)
            self.settings[name].setValidator(QDoubleValidator(*validator))
            self.settings[name].setMaxLength(length)


class TimePanel(CheckableGroupBox):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Focus Timing", parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_settings()
        self._set_restrictions()

    def _create_settings(self) -> None:
        settings = {
            "time_limit": "Time limit:",
            "break_time": "Break time:",
        }
        self.settings: Dict[str, LineEdit] = {}
        for name, description in settings.items():
            self.settings[name] = LineEdit()
            self._layout.addRow(description, self.settings[name])

        # sound warning is enabled in default
        self.warning = OptionCheckBox("enable sound warning")
        self.warning.setChecked(True)
        self._layout.addRow(self.warning)

    def _set_restrictions(self) -> None:
        # placeholder, validator
        restrictions = {
            "time_limit": ("1 ~ 59 (min)", (1, 59)),
            "break_time": ("1 ~ 59 (min)", (1, 59)),
        }

        for name, (placeholder, validator) in restrictions.items():
            self.settings[name].setPlaceholderText(placeholder)
            self.settings[name].setValidator(QIntValidator(*validator))


class AngleTolerance(IntEnum):
    """An IntEnum used to represent the angle options of PosturePanel.
    The int value is the angle allowed.
    """
    # Add member or modify value to provide more choices.
    LOOSE  = 25
    STRICT = 15

class PosturePanel(CheckableGroupBox):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Posture Detection", parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_settings()

    def _create_settings(self) -> None:
        group_box = QGroupBox("Allowed slope angle:")
        box_layout = QVBoxLayout()
        group_box.setLayout(box_layout)
        self._layout.addWidget(group_box)

        angles = [AngleTolerance.LOOSE, AngleTolerance.STRICT]
        self.angles: Dict[AngleTolerance, OptionRadioButton] = {}
        for tolerance in angles:
            self.angles[tolerance] = OptionRadioButton(f"{tolerance.name.lower()} ({tolerance})")
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
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Brightness Optimization", parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_slider()
        self._create_modes()

    def _create_slider(self) -> None:
        self.slider = HorizontalSlider()
        self._layout.addWidget(self.slider)

    def _create_modes(self) -> None:
        # name | description
        modes = {
            BrightnessMode.WEBCAM: "Webcam-based brightness detector \n(webcam required)",
            BrightnessMode.COLOR_SYSTEM: "Color-system mode",
        }
        self.modes: Dict[BrightnessMode, OptionCheckBox] = {}
        for mode, description in modes.items():
            self.modes[mode] = OptionCheckBox(description)
            self._layout.addWidget(self.modes[mode])

        # default mode
        self.modes[BrightnessMode.WEBCAM].setChecked(False)
        self.modes[BrightnessMode.COLOR_SYSTEM].setChecked(False)
