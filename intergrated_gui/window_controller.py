from typing import Dict, Tuple

from PyQt5.QtCore import QObject

from app.app_type import ApplicationType
from app.webcam_application import WebcamApplication
from intergrated_gui.panel_controller import PanelController
from intergrated_gui.window import Window
from util.task_worker import TaskWorker


class WindowController(QObject):
    def __init__(self, window: Window, app: WebcamApplication) -> None:
        super().__init__()

        self._window = window
        self._app = app
        self._panel_controller = PanelController(window.widgets["panel"], self._app)

        self._connect_app_and_information()
        self._connect_app_and_frame()
        self._connect_information_and_panel()
        self._start_app()

    def _start_app(self) -> None:
        self._worker = TaskWorker(self._app.start)
        self._thread = self._worker.run_in_thread(self._app.s_stopped)

    def _connect_app_and_information(self) -> None:
        information = self._window.widgets["information"]
        self._app.s_distance_refreshed.connect(information.update_distance)
        self._app.s_posture_refreshed.connect(information.update_posture)
        self._app.s_time_refreshed.connect(information.update_time)
        self._app.s_brightness_refreshed.connect(information.update_brightness)

    def _connect_app_and_frame(self) -> None:
        frame = self._window.widgets["frame"]
        self._app.s_frame_refreshed.connect(frame.set_frame)

    def _connect_information_and_panel(self) -> None:
        """First inits the show/hide state of information in accordance with the
        enabled state of panels, then connects the their state change.
        """
        info_widget = self._window.widgets["information"]
        panel_widget = self._window.widgets["panel"]

        # panel and its relative name of info
        relations: Dict[ApplicationType, Tuple[str, ...]] = {
            ApplicationType.DISTANCE_MEASUREMENT: ("distance",),
            ApplicationType.FOCUS_TIMING: ("time", "time-state"),
            ApplicationType.POSTURE_DETECTION: ("posture", "posture-detail"),
            ApplicationType.BRIGHTNESS_OPTIMIZATION: ("brightness",),
        }
        # init state
        for panel, infos in relations.items():
            for info in infos:
                if panel_widget.panels[panel].isChecked():
                    info_widget.show(info)
                else:
                    info_widget.hide(info)
        # connect change
        for panel, infos in relations.items():
            for info in infos:
                panel_widget.panels[panel].toggled.connect(
                    lambda checked, info=info:
                        info_widget.show(info)
                        if checked else
                        info_widget.hide(info)
                )
