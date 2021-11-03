import os
import screen_brightness_control as sbc
from PyQt5.QtCore import QObject

from configparser import ConfigParser
from distutils.util import strtobool
from intergrated_gui.panel_widget import AngleTolerance
from lib.brightness_calcuator import BrightnessMode
from lib.train import ModelPath

# Path of the config file.
CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")

class PanelController(QObject):
    def __init__(self, panel_widget, app):
        super().__init__()
        self._panel = panel_widget
        self._app = app

        self._load_configs()
        self._init_states()
        self._connect_signals()

    def _init_states(self):
        self._init_distance_states()
        self._init_time_states()
        self._init_posture_states()
        self._init_brightness_states()

    def _load_configs(self):
        """Load the configs and set init state of each mode and
        its following detailed widgets.
        The init state of the widgets will affect the initialization of app.
        """
        # Create a shared parser since they depends on the same config file.
        config = ConfigParser()
        config.read(CONFIG)

        panels = self._panel.panels

        # Enable modes that are set True.
        for mode, panel in panels.items():
            panel.setChecked(strtobool(config.get(mode, "checked")))

        # distance
        panels["distance"].settings["camera_dist"].setText(config.get("distance", "camera_dist"))
        panels["distance"].settings["warn_dist"].setText(config.get("distance", "warn_dist"))
        panels["distance"].warning.setChecked(strtobool(config.get("distance", "warning_enabled")))
    
        # time
        panels["time"].settings["time_limit"].setText(config.get("time", "time_limit"))
        panels["time"].settings["break_time"].setText(config.get("time", "break_time"))
        panels["time"].warning.setChecked(strtobool(config.get("time", "warning_enabled")))
        
        # posture
        if config.get("posture", "warn_angle") == "loose":
            panels["posture"].angles[AngleTolerance.LOOSE].setChecked(True)
        elif config.get("posture", "warn_angle") == "strict":
            panels["posture"].angles[AngleTolerance.STRICT].setChecked(True)
        if config.get("posture", "model_path") == "custom":
            panels["posture"].custom.setChecked(True)
        elif config.get("posture", "model_path") == "default":
            panels["posture"].custom.setChecked(False)
        panels["posture"].warning.setChecked(strtobool(config.get("posture", "warning_enabled")))
        
        # brightness
        panels["brightness"].slider.setValue(int(config.get("brightness", "slider_value")))
        if strtobool(config.get("brightness", "webcam_enabled")):
            panels["brightness"].modes[BrightnessMode.WEBCAM].setChecked(True)
        if strtobool(config.get("brightness", "color_system_enabled")):
            panels["brightness"].modes[BrightnessMode.COLOR_SYSTEM].setChecked(True)

    def _init_distance_states(self):
        panel = self._panel.panels["distance"]

        self._app.set_distance_measure(enabled=panel.isChecked())
        distance = panel.settings["camera_dist"]
        if distance.text():
            self._app.set_distance_measure(camera_dist=float(distance.text()))
        bound = panel.settings["warn_dist"]
        if bound.text():
            self._app.set_distance_measure(warn_dist=float(bound.text()))
        warning = panel.warning
        self._app.set_distance_measure(warning_enabled=warning.isChecked())

    def _init_time_states(self):
        panel = self._panel.panels["time"]

        self._app.set_focus_time(enabled=panel.isChecked())
        limit = panel.settings["time_limit"]
        if limit.text():
            self._app.set_focus_time(time_limit=int(limit.text()))
        break_ = panel.settings["break_time"]
        if break_.text():
            self._app.set_focus_time(break_time=int(break_.text()))
        warning = panel.warning
        self._app.set_focus_time(warning_enabled=warning.isChecked())

    def _init_posture_states(self):
        panel = self._panel.panels["posture"]

        self._app.set_posture_detect(enabled=panel.isChecked())
        if panel.angles[AngleTolerance.LOOSE].isChecked():
            self._app.set_posture_detect(warn_angle=AngleTolerance.LOOSE)
        else:
            self._app.set_posture_detect(warn_angle=AngleTolerance.STRICT)
        custom = panel.custom
        if custom.isChecked():
            self._app.set_posture_detect(model_path=ModelPath.CUSTOM)
        else:
            self._app.set_posture_detect(model_path=ModelPath.DEFAULT)
        warning = panel.warning
        self._app.set_posture_detect(warning_enabled=warning.isChecked())

    def _init_brightness_states(self):
        panel = self._panel.panels["brightness"]
        self._app.set_brightness_optimization(
            enabled=panel.isChecked(),
            slider_value=panel.slider.value(),
            webcam_enabled=panel.modes[BrightnessMode.WEBCAM].isChecked(),
            color_system_enabled=panel.modes[BrightnessMode.COLOR_SYSTEM].isChecked()
        )

    def _connect_signals(self):
        self._connect_distance_signals()
        self._connect_time_signals()
        self._connect_posture_signals()
        self._connect_brightness_signals()

    def _connect_distance_signals(self):
        panel = self._panel.panels["distance"]

        panel.toggled.connect(lambda checked: self._app.set_distance_measure(enabled=checked))
        distance = panel.settings["camera_dist"]
        distance.editingFinished.connect(lambda: self._app.set_distance_measure(camera_dist=float(distance.text())))
        bound = panel.settings["warn_dist"]
        bound.editingFinished.connect(lambda: self._app.set_distance_measure(warn_dist=float(bound.text())))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_distance_measure(warning_enabled=checked))

    def _connect_time_signals(self):
        panel = self._panel.panels["time"]

        panel.toggled.connect(lambda checked: self._app.set_focus_time(enabled=checked))
        limit = panel.settings["time_limit"]
        limit.editingFinished.connect(lambda: self._app.set_focus_time(time_limit=int(limit.text())))
        break_ = panel.settings["break_time"]
        break_.editingFinished.connect(lambda: self._app.set_focus_time(break_time=int(break_.text())))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_focus_time(warning_enabled=checked))

    def _connect_posture_signals(self):
        panel = self._panel.panels["posture"]

        panel.toggled.connect(lambda checked: self._app.set_posture_detect(enabled=checked))
        panel.angles[AngleTolerance.LOOSE].toggled.connect(lambda checked: self._app.set_posture_detect(warn_angle=AngleTolerance.LOOSE) if checked else None)
        panel.angles[AngleTolerance.STRICT].toggled.connect(lambda checked: self._app.set_posture_detect(warn_angle=AngleTolerance.STRICT) if checked else None)
        custom = panel.custom
        custom.toggled.connect(lambda checked: self._app.set_posture_detect(model_path=(ModelPath.CUSTOM if checked else ModelPath.DEFAULT)))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_posture_detect(warning_enabled=checked))

    def _connect_brightness_signals(self):
        panel = self._panel.panels["brightness"]

        panel.toggled.connect(lambda checked: self._app.set_brightness_optimization(enabled=checked))
        panel.slider.valueChanged.connect(lambda value: self._app.set_brightness_optimization(slider_value=value))
        panel.modes[BrightnessMode.WEBCAM].toggled.connect(lambda checked: self._app.set_brightness_optimization(webcam_enabled=checked))
        panel.modes[BrightnessMode.COLOR_SYSTEM].toggled.connect(lambda checked: self._app.set_brightness_optimization(color_system_enabled=checked))
