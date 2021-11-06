import os
from configparser import ConfigParser
from typing import Dict, Tuple

from PyQt5.QtCore import QObject, QThread, pyqtSlot

from gui.task_worker import TaskWorker
from intergrated_gui.panel_controller import PanelController
from intergrated_gui.window import Window
from lib.app_ import WebcamApplication

# Path of the config file.
CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")

class WindowController(QObject):
    def __init__(self, window: Window, app: WebcamApplication):
        super().__init__()

        self._window = window
        self._app = app
        self._panel_controller = PanelController(window.widgets["panel"], self._app)

        self._load_panel_configs()
        self._connect_app_and_information()
        self._connect_app_and_frame()
        self._connect_information_and_panel()
        self._connect_clean_up_signal()
        self._start_app()

    def _start_app(self) -> None:
        self._worker = TaskWorker(self._app.start)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        # Worker starts running after the thread is started.
        self._thread.started.connect(self._worker.run)
        # The job of thread and worker is finished after the App. calls stop.
        self._app.s_stopped.connect(self._thread.quit)
        self._app.s_stopped.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _connect_app_and_information(self) -> None:
        information = self._window.widgets["information"]
        self._app.s_distance_refreshed.connect(information.update_distance)
        self._app.s_posture_refreshed.connect(information.update_posture)
        self._app.s_time_refreshed.connect(information.update_time)
        self._app.s_brightness_refreshed.connect(information.update_brightness)
        self._app.s_grade_refreshed.connect(information.update_grade)

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
        relations: Dict[str, Tuple[str, ...]] = {
            "distance": ("distance",),
            "time": ("time", "time-state"),
            "posture": ("posture", "posture-detail"),
            "brightness": ("brightness",),
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
                    info_widget.show(info) if checked
                    else info_widget.hide(info)
                )

    def _connect_clean_up_signal(self) -> None:
        # Have the configs save before GUI being destroyed.
        self._window.set_clean_up_before_destroy(self._store_panel_configs)

    def _load_panel_configs(self) -> None:
        """Loads the configs of panel controller."""
        # Create a shared parser since they depends on the same config file.
        self._config = ConfigParser()
        self._config.read(CONFIG)

        self._panel_controller.load_configs(self._config)

    def _store_panel_configs(self) -> None:
        """Stores the configs of panel controller."""
        self._panel_controller.store_configs(self._config)
        # Save the states of all pages back to the config file all at once.
        with open(CONFIG, "w") as f:
            self._config.write(f)
