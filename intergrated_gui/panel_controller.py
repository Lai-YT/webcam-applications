import os
from configparser import ConfigParser

from PyQt5.QtCore import QCoreApplication, QEvent, QObject, Qt, pyqtSlot
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtWidgets import QFileDialog

from app.webcam_application_ import WebcamApplication
from brightness.calcuator import BrightnessMode
from intergrated_gui.panel_widget import AngleTolerance, PanelWidget
from posture.train import ModelPath


class PanelController(QObject):
    def __init__(self, panel_widget: PanelWidget, app: WebcamApplication) -> None:
        super().__init__()
        self._panel = panel_widget
        self._app = app
        # Connect signals first to make sure the init states can trigger their
        # corresponding methods.
        self._connect_signals()
        self._init_states()

    def _init_states(self) -> None:
        self._init_distance_states()
        self._init_time_states()
        self._init_posture_states()
        self._init_brightness_states()

    def load_configs(self, config: ConfigParser) -> None:
        """Loads the configs and set init state of each mode
        and its following detailed widgets.

        The init state of the widgets will affect the initialization of app.
        """
        panels = self._panel.panels

        # Enable modes that are set True.
        for mode, panel in panels.items():
            panel.setChecked(config.getboolean(mode, "checked"))

        # A simple setText does not trigger the editingFinished signal since
        # no enter or return key is pressed. So send a return pressed event
        # everytime after the setText to act like a manual user.
        return_pressed_event = QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier)

        # distance
        for name, line_edit in panels["distance"].settings.items():
            line_edit.setText(config.get("distance", name))
            QCoreApplication.sendEvent(line_edit, return_pressed_event)
        panels["distance"].warning.setChecked(config.getboolean("distance", "warning_enabled"))
        # time
        for name, line_edit in panels["time"].settings.items():
            line_edit.setText(config.get("time", name))
            QCoreApplication.sendEvent(line_edit, return_pressed_event)
        panels["time"].warning.setChecked(config.getboolean("time", "warning_enabled"))
        # posture
        if config.get("posture", "warn_angle") == "loose":
            panels["posture"].angles[AngleTolerance.LOOSE].setChecked(True)
        elif config.get("posture", "warn_angle") == "strict":
            panels["posture"].angles[AngleTolerance.STRICT].setChecked(True)
        if config.get("posture", "model_path") == "custom":
            panels["posture"].custom.setChecked(True)
        elif config.get("posture", "model_path") == "default":
            panels["posture"].custom.setChecked(False)
        panels["posture"].warning.setChecked(config.getboolean("posture", "warning_enabled"))
        # brightness
        panels["brightness"].slider.setValue(config.getint("brightness", "slider_value"))
        if config.getboolean("brightness", "webcam_enabled"):
            panels["brightness"].modes[BrightnessMode.WEBCAM].setChecked(True)
        if config.getboolean("brightness", "color_system_enabled"):
            panels["brightness"].modes[BrightnessMode.COLOR_SYSTEM].setChecked(True)

    def store_configs(self, config: ConfigParser) -> None:
        """Stores data of each mode and its following detailed widgets
        in the configs.
        """
        panels = self._panel.panels

        # Set true if the group box is checked.
        for section, check_box in panels.items():
            config.set(section, "checked", str(check_box.isChecked()))

        # distance
        for name, line_edit in panels["distance"].settings.items():
            config.set("distance", name, line_edit.text())
        config.set("distance", "warning_enabled",
            str(panels["distance"].warning.isChecked()))
        # time
        for name, line_edit in panels["time"].settings.items():
            config.set("time", name, line_edit.text())
        config.set("time", "warning_enabled",
            str(panels["distance"].warning.isChecked()))
        # posture
        config.set("posture", "warn_angle",
            "loose" if panels["posture"].angles[AngleTolerance.LOOSE].isChecked() else "strict")
        config.set("posture", "model_path",
            "custom" if panels["posture"].custom.isChecked() else "default")
        config.set("posture", "warning_enabled",
            str(panels["distance"].warning.isChecked()))
        # brightness
        config.set("brightness", "slider_value",
            str(panels["brightness"].slider.value()))
        config.set("brightness", "webcam_enabled",
            str(panels["brightness"].modes[BrightnessMode.WEBCAM].isChecked()))
        config.set("brightness", "color_system_enabled",
            str(panels["brightness"].modes[BrightnessMode.COLOR_SYSTEM].isChecked()))

    def _init_distance_states(self) -> None:
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

    def _init_time_states(self) -> None:
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

    def _init_posture_states(self) -> None:
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

    def _init_brightness_states(self) -> None:
        panel = self._panel.panels["brightness"]
        self._app.set_brightness_optimization(
            enabled=panel.isChecked(),
            slider_value=panel.slider.value(),
            webcam_enabled=panel.modes[BrightnessMode.WEBCAM].isChecked(),
            color_system_enabled=panel.modes[BrightnessMode.COLOR_SYSTEM].isChecked()
        )

    def _connect_signals(self) -> None:
        self._connect_distance_signals()
        self._connect_time_signals()
        self._connect_posture_signals()
        self._connect_brightness_signals()

    def _connect_distance_signals(self) -> None:
        panel = self._panel.panels["distance"]
        panel.toggled.connect(lambda checked: self._app.set_distance_measure(enabled=checked))
        panel.file_open.clicked.connect(self._choose_file_path)
        distance = panel.settings["camera_dist"]
        distance.editingFinished.connect(lambda: self._app.set_distance_measure(camera_dist=float(distance.text())))
        bound = panel.settings["warn_dist"]
        bound.editingFinished.connect(lambda: self._app.set_distance_measure(warn_dist=float(bound.text())))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_distance_measure(warning_enabled=checked))

    def _choose_file_path(self) -> None:
        filename, *_ =  QFileDialog.getOpenFileName(
            self._panel.panels["distance"], "Open File", "C:\\", "Images (*.png *.jpg)")
        self._panel.panels["distance"].img_path.setText(os.path.basename(filename))

    def _connect_time_signals(self) -> None:
        panel = self._panel.panels["time"]

        panel.toggled.connect(lambda checked: self._app.set_focus_time(enabled=checked))
        limit = panel.settings["time_limit"]
        limit.editingFinished.connect(lambda: self._app.set_focus_time(time_limit=int(limit.text())))
        break_ = panel.settings["break_time"]
        break_.editingFinished.connect(lambda: self._app.set_focus_time(break_time=int(break_.text())))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_focus_time(warning_enabled=checked))

    def _connect_posture_signals(self) -> None:
        panel = self._panel.panels["posture"]

        panel.toggled.connect(lambda checked: self._app.set_posture_detect(enabled=checked))
        panel.angles[AngleTolerance.LOOSE].toggled.connect(lambda checked: self._app.set_posture_detect(warn_angle=AngleTolerance.LOOSE) if checked else None)
        panel.angles[AngleTolerance.STRICT].toggled.connect(lambda checked: self._app.set_posture_detect(warn_angle=AngleTolerance.STRICT) if checked else None)
        custom = panel.custom
        custom.toggled.connect(lambda checked: self._app.set_posture_detect(model_path=(ModelPath.CUSTOM if checked else ModelPath.DEFAULT)))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_posture_detect(warning_enabled=checked))

    def _connect_brightness_signals(self) -> None:
        panel = self._panel.panels["brightness"]

        panel.toggled.connect(lambda checked: self._app.set_brightness_optimization(enabled=checked))
        panel.slider.valueChanged.connect(lambda value: self._app.set_brightness_optimization(slider_value=value))
        panel.modes[BrightnessMode.WEBCAM].toggled.connect(lambda checked: self._app.set_brightness_optimization(webcam_enabled=checked))
        panel.modes[BrightnessMode.COLOR_SYSTEM].toggled.connect(lambda checked: self._app.set_brightness_optimization(color_system_enabled=checked))
