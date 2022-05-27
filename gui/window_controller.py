import atexit
from configparser import ConfigParser
from datetime import datetime
from typing import Dict, Tuple

from PyQt5.QtCore import QObject
import numpy as np
import requests

import concentration.fuzzy.parse as parse
import server.main as flask_server
import server.post as poster
from app.app_type import ApplicationType
from app.webcam_application import WebcamApplication
from concentration.fuzzy.classes import Interval
from gui.language import Language
from gui.panel_controller import PanelController
from gui.window import Window
from util.path import to_abs_path
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
        self._connect_config_change()

        self._server_url = f"http://{flask_server.HOST}:{flask_server.PORT}"
        self._connect_grade_output_routines()
        self._connect_slices_post()

        # These configurations are handled by windows since they have not much
        # to do with app.
        self._CONFIG_FILE = to_abs_path("./gui/config.ini")
        self._init_global_config()
        atexit.register(self._store_global_config)

        self._start_app()

    def _start_app(self) -> None:
        self._worker = TaskWorker(self._app.start)
        self._app.s_stopped.connect(self._worker.quit)
        self._worker.start()

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
                    lambda checked, info=info: info_widget.show(info)
                    if checked
                    else info_widget.hide(info)
                )

    def _connect_config_change(self) -> None:
        # index is designed to be as same as the value of enum Language
        self._window.widgets["config"].combox.currentIndexChanged.connect(
            self._change_language_of_widgets
        )

        def update_id_config(student_id: str) -> None:
            self._student_id = student_id

        self._window.widgets["config"].id.textChanged.connect(update_id_config)

    def _connect_grade_output_routines(self) -> None:
        self._json_file: str = to_abs_path("intervals.json")
        parse.init_json(self._json_file)
        self._app.s_concent_interval_refreshed.connect(self._write_grade_into_json)

        self._app.s_concent_interval_refreshed.connect(self._send_grade_to_server)

    def _connect_slices_post(self) -> None:
        self._app.s_screenshot_refreshed.connect(self._send_slices_to_server)

    def _send_grade_to_server(self, interval: Interval) -> None:
        grade = interval.__dict__
        # add new key info
        grade["time"] = datetime.fromtimestamp(interval.end).strftime(
            poster.DATE_STR_FORMAT
        )
        grade["id"] = self._student_id
        try:
            requests.post(f"{self._server_url}/grade", json=grade)
        except requests.ConnectionError:
            # Skip posting if the connection fails,
            # which may be caused by server not running.
            pass

    def _write_grade_into_json(self, interval: Interval) -> None:
        parse.append_to_json(self._json_file, interval.__dict__)

    def _send_slices_to_server(self, slices: np.ndarray) -> None:
        data = {
            "id": self._student_id,
            "slices": slices.tolist(),  # ndarray is not JSON serializable
        }
        try:
            requests.post(f"{self._server_url}/screenshot", json=data)
        except requests.ConnectionError:
            # Skip posting if the connection fails,
            # which may be caused by server not running.
            pass

    def _change_language_of_widgets(self, lang_no: int) -> None:
        self._lang = Language(lang_no)
        for widget in self._window.widgets.values():
            widget.change_language(self._lang)

    def _init_global_config(self) -> None:
        """Initializes student id and language of window."""
        # Try to reduce the memory comsumption by delete-after-use.
        self._load_global_config()
        self._student_id = self._config.get("GLOBAL", "id")
        self._lang = Language[self._config.get("GLOBAL", "language")]
        del self._config

        self._window.widgets["config"].id.setText(self._student_id)
        self._window.widgets["config"].combox.setCurrentIndex(self._lang.value)

    def _load_global_config(self) -> None:
        self._config = ConfigParser()
        self._config.read(self._CONFIG_FILE, encoding="utf-8")

    def _store_global_config(self) -> None:
        """Writes the current global configurations back into the config file."""
        self._load_global_config()

        self._config["GLOBAL"]["language"] = self._lang.name
        self._config["GLOBAL"]["id"] = self._student_id

        with open(self._CONFIG_FILE, "w", encoding="utf-8") as f:
            self._config.write(f)
