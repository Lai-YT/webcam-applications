from PyQt5.QtCore import QObject


class PanelController(QObject):
    def __init__(self, panel_widget: "PanelWidget"):
        super().__init__()
        self._panel = panel_widget

        self.states = {
            "distance": {
                "enabled": None,
                "width": None,
                "distance": None,
                "bound": None,
                "warning": None,
            },
            "time": {
                "enabled": None,
                "limit": None,
                "break": None,
                "warning": None,
            },
            "posture": {
                "enabled": None,
                "angle": None,
                "warning": None,
                "customized": None,
            },
            "brightness": {
                "enabled": None,
                "webcam": None,
                "color-system": None,
            },
        }
        self._init_states()
        self._connect_signals()
        # test
        for panel, state in self.states.items():
            print(panel)
            print(state)

    def _init_states(self):
        self._init_distance_states()
        self._init_time_states()
        self._init_posture_signals()
        self._init_brightness_states()

    def _set_state(self, app_kind, param_name, new_value):
        self.states[app_kind][param_name] = new_value

    def _init_distance_states(self):
        panel = self._panel.panels["distance"]

        self._set_state("distance", "enabled", panel.isChecked())
        width = panel.settings["width"]
        if width.text():
            self._set_state("distance", "width", float(width.text()))
        distance = panel.settings["distance"]
        if distance.text():
            self._set_state("distance", "distance", float(distance.text()))
        bound = panel.settings["bound"]
        if bound.text():
            self._set_state("distance", "bound", float(bound.text()))
        warning = panel.warning
        self._set_state("distance", "warning", warning.isChecked())

    def _init_time_states(self):
        panel = self._panel.panels["time"]

        self._set_state("time", "enabled", panel.isChecked())
        limit = panel.settings["limit"]
        if limit.text():
            self._set_state("time", "limit", int(limit.text()))
        break_ = panel.settings["break"]
        if break_.text():
            self._set_state("time", "break", int(break_.text()))
        warning = panel.warning
        self._set_state("time", "warning", warning.isChecked())

    def _init_posture_signals(self):
        panel = self._panel.panels["posture"]

        self._set_state("posture", "enabled", panel.isChecked())
        angle = panel.settings["angle"]
        if angle.text():
            self._set_states("posture", "angle", float(angle.text()))
        custom = panel.custom
        self._set_state("posture", "customized", custom.isChecked())
        warning = panel.warning
        self._set_state("posture", "customized", warning.isChecked())

    def _init_brightness_states(self):
        panel = self._panel.panels["brightness"]

        self._set_state("brightness", "enabled", panel.isChecked())
        self._set_state("brightness", "webcam", panel.modes["webcam"].isChecked())
        self._set_state("brightness", "color-system", panel.modes["color-system"].isChecked())
        warning = panel.warning
        self._set_state("brightness", "warning", warning.isChecked())

    def _connect_signals(self):
        self._connect_distance_signals()
        self._connect_time_signals()
        self._connect_posture_signals()
        self._connect_brightness_signals()

    def _connect_distance_signals(self):
        panel = self._panel.panels["distance"]

        width = panel.settings["width"]
        width.editingFinished.connect(lambda: self._set_state("distance", "width", float(width.text())))
        distance = panel.settings["distance"]
        distance.editingFinished.connect(lambda: self._set_state("distance", "distance", float(distance.text())))
        bound = panel.settings["bound"]
        bound.editingFinished.connect(lambda: self._set_state("distance", "bound", float(bound.text())))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._set_state("distance", "warning", checked))

    def _connect_time_signals(self):
        panel = self._panel.panels["time"]

        limit = panel.settings["limit"]
        limit.editingFinished.connect(lambda: self._set_state("time", "limit", int(limit.text())))
        break_ = panel.settings["break"]
        break_.editingFinished.connect(lambda: self._set_state("time", "break", int(break_.text())))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._set_state("time", "warning", checked))

    def _connect_posture_signals(self):
        panel = self._panel.panels["posture"]

        angle = panel.settings["angle"]
        angle.editingFinished.connect(lambda: self._set_state("posture", "angle", float(angle.text())))
        custom = panel.custom
        custom.toggled.connect(lambda checked: self._set_state("posture", "customized", checked))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._set_state("posture", "warning", checked))

    def _connect_brightness_signals(self):
        panel = self._panel.panels["brightness"]

        panel.modes["webcam"].toggled.connect(lambda checked: self._set_state("brightness", "webcam", checked))
        panel.modes["color-system"].toggled.connect(lambda checked: self._set_state("brightness", "color-system", checked))
        warning = panel.warning
        warning.toggled.connect(lambda checked: self._set_state("brightness", "warning", checked))
