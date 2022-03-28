from configparser import ConfigParser
from functools import partial

from PyQt5.QtCore import QObject
from PyQt5.QtWidgets import QFileDialog

from app.app_type import ApplicationType
from app.webcam_application import WebcamApplication
from brightness.calculator import BrightnessMode
from gui.panel_widget import AngleTolerance, PanelWidget


class PanelController(QObject):
    def __init__(self, panel_widget: PanelWidget, app: WebcamApplication) -> None:
        super().__init__()
        self._panel_widget = panel_widget
        self._app = app
        self._init_panels()
        # Connect signals first to make sure the init states can trigger their
        # corresponding methods.
        self._connect_signals()

    def _init_panels(self) -> None:
        settings: ConfigParser = self._app.get_settings()

        # Enable apps that are enabled.
        for app_type, panel in self._panel_widget.panels.items():
            panel.setChecked(settings.getboolean(app_type.name, "ENABLED"))

        self._init_distance_panel(settings)
        self._init_time_panel(settings)
        self._init_posture_panel(settings)
        self._init_brightness_panel(settings)

    def _init_distance_panel(self, settings: ConfigParser) -> None:
        app_type = ApplicationType.DISTANCE_MEASUREMENT
        panel = self._panel_widget.panels[app_type]

        panel.settings["camera_dist"].setText(settings.get(app_type.name, "REFERENCE_DISTANCE"))
        panel.settings["warn_dist"].setText(settings.get(app_type.name, "LIMIT"))
        panel.file_path.setText(settings.get(app_type.name, "REFERENCE_IMAGE_PATH"))
        panel.warning.setChecked(settings.getboolean(app_type.name, "WARNING"))

    def _init_time_panel(self, settings: ConfigParser) -> None:
        app_type = ApplicationType.FOCUS_TIMING
        panel = self._panel_widget.panels[app_type]

        panel.settings["time_limit"].setText(settings.get(app_type.name, "LIMIT"))
        panel.settings["break_time"].setText(settings.get(app_type.name, "BREAK_TIME"))
        panel.warning.setChecked(settings.getboolean(app_type.name, "WARNING"))

    def _init_posture_panel(self, settings: ConfigParser) -> None:
        app_type = ApplicationType.POSTURE_DETECTION
        panel = self._panel_widget.panels[app_type]

        angle = settings.getint(app_type.name, "ANGLE")
        panel.angles[AngleTolerance(angle)].setChecked(True)
        panel.warning.setChecked(settings.getboolean(app_type.name, "WARNING"))

    def _init_brightness_panel(self, settings: ConfigParser) -> None:
        app_type = ApplicationType.BRIGHTNESS_OPTIMIZATION
        panel = self._panel_widget.panels[app_type]

        panel.slider.setValue(settings.getint(app_type.name, "BASE_VALUE"))
        mode: str = settings.get(app_type.name, "MODE")  # name of enum
        mode_type = BrightnessMode[mode]
        panel.modes[BrightnessMode.WEBCAM].setChecked(
            mode_type in (BrightnessMode.WEBCAM, BrightnessMode.BOTH)
        )
        panel.modes[BrightnessMode.COLOR_SYSTEM].setChecked(
            mode_type in (BrightnessMode.COLOR_SYSTEM, BrightnessMode.BOTH)
        )

    def _connect_signals(self) -> None:
        self._connect_distance_signals()
        self._connect_time_signals()
        self._connect_posture_signals()
        self._connect_brightness_signals()

    def _connect_distance_signals(self) -> None:
        panel = self._panel_widget.panels[ApplicationType.DISTANCE_MEASUREMENT]

        panel.toggled.connect(
            lambda checked: self._app.set_distance_measure(enabled=checked)
        )
        # file_open -> (connect) choose file -> (Call) setText
        # -> (emit) textChanged -> (connect) set_path
        panel.file_open.clicked.connect(self._choose_file_path)
        panel.file_path.textChanged.connect(
            lambda path: self._app.set_distance_measure(ref_img_path=path)
        )
        distance = panel.settings["camera_dist"]
        distance.editingFinished.connect(
            lambda: self._app.set_distance_measure(camera_dist=float(distance.text()))
        )
        bound = panel.settings["warn_dist"]
        bound.editingFinished.connect(
            lambda: self._app.set_distance_measure(warn_dist=float(bound.text()))
        )
        panel.warning.toggled.connect(
            lambda checked: self._app.set_distance_measure(warning_enabled=checked)
        )

    def _choose_file_path(self) -> None:
        panel = self._panel_widget.panels[ApplicationType.DISTANCE_MEASUREMENT]
        root = panel.file_path.text() if panel.file_path.text() else "C:\\"
        filename, *_ =  QFileDialog.getOpenFileName(
            panel, "Open File", root, "Images (*.png *.jpg)")
        # the choose may be cancelled
        if filename:
            panel.file_path.setText(filename)

    def _connect_time_signals(self) -> None:
        panel = self._panel_widget.panels[ApplicationType.FOCUS_TIMING]

        panel.toggled.connect(
            lambda checked: self._app.set_focus_time(enabled=checked)
        )
        limit = panel.settings["time_limit"]
        limit.editingFinished.connect(
            lambda: self._app.set_focus_time(time_limit=int(limit.text()))
        )
        break_ = panel.settings["break_time"]
        break_.editingFinished.connect(
            lambda: self._app.set_focus_time(break_time=int(break_.text()))
        )
        panel.warning.toggled.connect(
            lambda checked: self._app.set_focus_time(warning_enabled=checked)
        )

    def _connect_posture_signals(self) -> None:
        panel = self._panel_widget.panels[ApplicationType.POSTURE_DETECTION]

        def change_tolerance_angle(checked: bool, angle: AngleTolerance) -> None:
            """Sets the corresponding angle if is checked."""
            if checked:
                self._app.set_posture_detect(warn_angle=angle)

        panel.toggled.connect(
            lambda checked: self._app.set_posture_detect(enabled=checked)
        )
        for angle in AngleTolerance:
            panel.angles[angle].toggled.connect(
                partial(change_tolerance_angle, angle=angle)
            )
        panel.warning.toggled.connect(
            lambda checked: self._app.set_posture_detect(warning_enabled=checked)
        )

    def _connect_brightness_signals(self) -> None:
        panel = self._panel_widget.panels[ApplicationType.BRIGHTNESS_OPTIMIZATION]

        def get_brightness_mode() -> BrightnessMode:
            """Returns the brightness mode determined by the combination of
            checked buttons.
            """
            if (panel.modes[BrightnessMode.WEBCAM].isChecked()
                    and panel.modes[BrightnessMode.COLOR_SYSTEM].isChecked()):
                return BrightnessMode.BOTH
            if panel.modes[BrightnessMode.WEBCAM].isChecked():
                return BrightnessMode.WEBCAM
            if panel.modes[BrightnessMode.COLOR_SYSTEM].isChecked():
                return BrightnessMode.COLOR_SYSTEM
            return BrightnessMode.MANUAL

        panel.toggled.connect(
            lambda checked: self._app.set_brightness_optimization(enabled=checked)
        )
        panel.slider.valueChanged.connect(
            lambda value: self._app.set_brightness_optimization(slider_value=value)
        )
        for mode in (BrightnessMode.WEBCAM, BrightnessMode.COLOR_SYSTEM):
            panel.modes[mode].toggled.connect(
                lambda: self._app.set_brightness_optimization(mode=get_brightness_mode())
            )
