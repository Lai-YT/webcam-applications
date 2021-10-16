from PyQt5.QtCore import QObject

from lib.train import ModelPath
from intergrated_gui.panel_widget import AngleTolerance


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
        self._init_posture_signals()
        self._init_brightness_states()

    def _init_distance_states(self):
        panel = self._panel.panels["distance"]

        self._app.set_distance_measure(enabled=panel.isChecked())
        distance = panel.settings["distance"]
        if distance.text():
            self._app.set_distance_measure(camera_dist=float(distance.text()))
        bound = panel.settings["bound"]
        if bound.text():
            self._app.set_distance_measure(warn_dist=float(bound.text()))
        warning = panel.warning
        self._app.set_distance_measure(warning_enabled=warning.isChecked())

    def _init_time_states(self):
        panel = self._panel.panels["time"]

        self._app.set_focus_time(enabled=panel.isChecked())
        limit = panel.settings["limit"]
        if limit.text():
            self._app.set_focus_time(time_limit=int(limit.text()))
        break_ = panel.settings["break"]
        if break_.text():
            self._app.set_focus_time(break_time=int(break_.text()))
        warning = panel.warning
        self._app.set_focus_time(warning_enabled=warning.isChecked())

    def _init_posture_signals(self):
        panel = self._panel.panels["posture"]

        self._app.set_posture_detect(enabled=panel.isChecked())
        self._app.set_posture_detect(warn_angle=(AngleTolerance.LOOSE if panel.angles[AngleTolerance.LOOSE].isChecked() else AngleTolerance.STRICT))
        custom = panel.custom
        self._app.set_posture_detect(model_path=(ModelPath.custom if custom.isChecked() else ModelPath.default))
        warning = panel.warning
        self._app.set_posture_detect(warning_enabled=warning.isChecked())

    def _init_brightness_states(self):
        pass

    def _connect_signals(self):
        self._connect_distance_signals()
        self._connect_time_signals()
        self._connect_posture_signals()
        self._connect_brightness_signals()

    def _connect_distance_signals(self):
        panel = self._panel.panels["distance"]

        panel.toggled.connect(lambda checked: self._app.set_distance_measure(enabled=checked))
        distance = panel.settings["distance"]
        distance.editingFinished.connect(lambda: self._app.set_distance_measure(camera_dist=float(distance.text())))
        bound = panel.settings["bound"]
        bound.editingFinished.connect(lambda: self._app.set_distance_measure(warn_dist=float(bound.text())))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_distance_measure(warning_enabled=checked))

    def _connect_time_signals(self):
        panel = self._panel.panels["time"]

        panel.toggled.connect(lambda checked: self._app.set_focus_time(enabled=checked))
        limit = panel.settings["limit"]
        limit.editingFinished.connect(lambda: self._app.set_focus_time(time_limit=int(limit.text())))
        break_ = panel.settings["break"]
        break_.editingFinished.connect(lambda: self._app.set_focus_time(break_time=int(break_.text())))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_focus_time(warning_enabled=checked))

    def _connect_posture_signals(self):
        panel = self._panel.panels["posture"]

        panel.toggled.connect(lambda checked: self._app.set_posture_detect(enabled=checked))
        panel.angles[AngleTolerance.LOOSE].toggled.connect(lambda checked: self._app.set_posture_detect(warn_angle=AngleTolerance.LOOSE) if checked else None)
        panel.angles[AngleTolerance.STRICT].toggled.connect(lambda checked: self._app.set_posture_detect(warn_angle=AngleTolerance.STRICT) if checked else None)
        custom = panel.custom
        custom.toggled.connect(lambda checked: self._app.set_posture_detect(model_path=(ModelPath.custom if checked else ModelPath.default)))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._app.set_posture_detect(warning_enabled=checked))

    def _connect_brightness_signals(self):
        pass
