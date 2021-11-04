import os
from PyQt5.QtCore import QObject, pyqtSlot

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

        self._init_states()
        self._connect_signals()

    def _init_states(self):
        self._init_distance_states()
        self._init_time_states()
        self._init_posture_states()
        self._init_brightness_states()

    def load_configs(self, config):
        """Load the configs and set init state of each mode and
        its following detailed widgets.
        The init state of the widgets will affect the initialization of app.
        """
        panels = self._panel.panels

        # Enable modes that are set True.
        for mode, panel in panels.items():
            panel.setChecked(strtobool(config.get(mode, "checked")))

        # distance
        for name, line_edit in panels["distance"].settings.items():
            line_edit.setText(config.get("distance", name))
        panels["distance"].warning.setChecked(strtobool(config.get("distance", "warning_enabled")))
        # time
        for name, line_edit in panels["time"].settings.items():
            line_edit.setText(config.get("time", name))
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

    def store_configs(self, config):
        """Store data of each mode and its following detailed widgets 
        in the configs."""
        panels = self._panel.panels

        # Set true if the group box is checked.
        for section, check_box in panels.items():
            config.set(section, "checked", "True" if check_box.isChecked() else "False")

        # distance
        for name, line_edit in panels["distance"].settings.items():
            config.set("distance", name, line_edit.text())
        config.set("distance", "warning_enabled", 
            "True" if panels["distance"].warning.isChecked() else "False")
        # time
        for name, line_edit in panels["time"].settings.items():
            config.set("time", name, line_edit.text())
        config.set("time", "warning_enabled", 
            "True" if panels["distance"].warning.isChecked() else "False")
        # posture
        config.set("posture", "warn_angle",
            "loose" if panels["posture"].angles[AngleTolerance.LOOSE].isChecked() else "strict")
        config.set("posture", "model_path",
            "custom" if panels["posture"].custom.isChecked() else "default")
        config.set("posture", "warning_enabled", 
            "True" if panels["distance"].warning.isChecked() else "False")
        # brightness
        config.set("brightness", "slider_value", str(panels["brightness"].slider.value()))
        config.set("brightness", "webcam_enabled",
            "True" if panels["brightness"].modes[BrightnessMode.WEBCAM].isChecked() else "False")
        config.set("brightness", "color_system_enabled",
            "True" if panels["brightness"].modes[BrightnessMode.COLOR_SYSTEM].isChecked() else "False")

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
