import json
from enum import IntEnum
from typing import Dict

from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QVBoxLayout, QWidget,
)

from app.app_type import ApplicationType
from brightness.calculator import BrightnessMode
from gui.component import (
    ActionButton, CheckableGroupBox, HorizontalSlider, Label, LineEdit,
    OptionCheckBox, OptionRadioButton,
)
from gui.language import Language
from util.path import to_abs_path


class PanelWidget(QWidget):
    """A widget which contains the views of applications."""

    SOUND_ENABLE_TEXT = "enable sound warning"

    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)

        self.panels: Dict[ApplicationType, CheckableGroupBox] = {
            ApplicationType.DISTANCE_MEASUREMENT: DistancePanel(),
            ApplicationType.FOCUS_TIMING: TimePanel(),
            ApplicationType.POSTURE_DETECTION: PosturePanel(),
            ApplicationType.BRIGHTNESS_OPTIMIZATION: BrightnessPanel(),
        }

        layout = QVBoxLayout()
        for panel in self.panels.values():
            layout.addWidget(panel, stretch=1)

        layout.addStretch(5)
        self.setLayout(layout)

    def change_language(self, lang: Language) -> None:
        """Passes the language change request to all panels."""
        self._lang_file = to_abs_path(f"./gui/lang/{lang.name.lower()}.json")
        lang_map = self._get_language_map()
        for panel in self.panels.values():
            panel.change_language(lang_map[type(panel).__name__])

    def _get_language_map(self) -> Dict[str, Dict[str, str]]:
        with open(self._lang_file, mode="r", encoding="utf-8") as f:
            return json.load(f)


class DistancePanel(CheckableGroupBox):
    """A view which contains the settings of distance measurement."""
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Distance Measurement", parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_settings()
        self._set_restrictions()

    def change_language(self, lang_map: Dict[str, str]) -> None:
        self.setTitle(lang_map["title"])
        self._file_path_layout.itemAt(0).widget().setText(lang_map["reference"])
        self.file_open.setText(lang_map["open"])
        self._layout.itemAt(1, QFormLayout.LabelRole).widget().setText(lang_map["camera_dist"])
        self._layout.itemAt(2, QFormLayout.LabelRole).widget().setText(lang_map["warn_dist"])
        self.settings["camera_dist"].setPlaceholderText(lang_map["camera_restriction"])
        self.settings["warn_dist"].setPlaceholderText(lang_map["warn_restriction"])
        self.warning.setText(lang_map["warning"])

    def _create_settings(self) -> None:
        # the file path line and button are in their own layout
        self._file_path_layout = QHBoxLayout()
        self._file_path_layout.addWidget(Label("Reference:"))

        self.file_path = LineEdit()
        self.file_path.setReadOnly(True)
        self._file_path_layout.addWidget(self.file_path)

        self.file_open = ActionButton("Open File...")
        self._file_path_layout.addWidget(self.file_open)

        self._layout.setLayout(0, QFormLayout.SpanningRole, self._file_path_layout)

        settings = {
            "camera_dist": "Distance in reference:",
            "warn_dist": "Shortest distance allowed:",
        }
        self.settings: Dict[str, LineEdit] = {}
        for name, description in settings.items():
            self.settings[name] = LineEdit()
            self._layout.addRow(description, self.settings[name])

        # sound warning is enabled in default
        self.warning = OptionCheckBox(PanelWidget.SOUND_ENABLE_TEXT)
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
    """A view which contains the settings of focus timing."""
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Focus Timing", parent)

        self._layout = QFormLayout()
        self.setLayout(self._layout)

        self._create_settings()
        self._set_restrictions()

    def change_language(self, lang_map: Dict[str, str]) -> None:
        self.setTitle(lang_map["title"])
        self._layout.itemAt(0, QFormLayout.LabelRole).widget().setText(lang_map["limit"])
        self._layout.itemAt(1, QFormLayout.LabelRole).widget().setText(lang_map["break"])
        self.settings["time_limit"].setPlaceholderText(lang_map["limit_restriction"])
        self.settings["break_time"].setPlaceholderText(lang_map["break_restriction"])
        self.warning.setText(lang_map["warning"])

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
        self.warning = OptionCheckBox(PanelWidget.SOUND_ENABLE_TEXT)
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
    """A view which contains the settings of posture detection."""
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Posture Detection", parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_settings()

    def change_language(self, lang_map: Dict[str, str]) -> None:
        self.setTitle(lang_map["title"])
        self._layout.itemAt(0).widget().setTitle(lang_map["group_title"])
        for tolerance in AngleTolerance:
            self.angles[tolerance].setText(lang_map[tolerance.name.lower()])
        self.warning.setText(lang_map["warning"])

    def _create_settings(self) -> None:
        group_box = QGroupBox("Allowed slope angle:")
        box_layout = QVBoxLayout()
        group_box.setLayout(box_layout)
        self._layout.addWidget(group_box)

        self.angles: Dict[AngleTolerance, OptionRadioButton] = {}
        for tolerance in AngleTolerance:
            btn = OptionRadioButton(f"{tolerance.name.lower()} ({tolerance})")
            self.angles[tolerance] = btn
            box_layout.addWidget(btn)
        # a loose angle tolerance is used in default
        self.angles[AngleTolerance.LOOSE].setChecked(True)

        # sound warning is enabled in default
        self.warning = OptionCheckBox(PanelWidget.SOUND_ENABLE_TEXT)
        self.warning.setChecked(True)
        self._layout.addWidget(self.warning)


class BrightnessPanel(CheckableGroupBox):
    """A view which contains which the settings of brightness optimization."""
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__("Brightness Optimization", parent)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_slider()
        self._create_modes()

    def change_language(self, lang_map: Dict[str, str]) -> None:
        self.setTitle(lang_map["title"])
        for mode in (BrightnessMode.WEBCAM, BrightnessMode.COLOR_SYSTEM):
            self.modes[mode].setText(lang_map[mode.name.lower()])

    def _create_slider(self) -> None:
        self.slider = HorizontalSlider()
        self._layout.addWidget(self.slider)

    def _create_modes(self) -> None:
        # name | description
        modes: Dict[BrightnessMode, str] = {
            BrightnessMode.WEBCAM: ("Webcam-based brightness detector \n"
                                    "(webcam required)"),
            BrightnessMode.COLOR_SYSTEM: "Color-system mode",
        }
        self.modes: Dict[BrightnessMode, OptionCheckBox] = {}
        for mode, description in modes.items():
            self.modes[mode] = OptionCheckBox(description)
            self._layout.addWidget(self.modes[mode])

        # default mode
        self.modes[BrightnessMode.WEBCAM].setChecked(False)
        self.modes[BrightnessMode.COLOR_SYSTEM].setChecked(False)
