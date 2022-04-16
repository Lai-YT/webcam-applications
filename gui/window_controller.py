from configparser import ConfigParser
from datetime import datetime
from typing import Dict, Tuple

from PyQt5.QtCore import QObject
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
        self._connect_language_change()
        self._connect_grade_output_routines()

        # language configuration is handled by windows since it's not part of app
        self._LANGUAGE_CONFIG = to_abs_path("./gui/lang/language.ini")
        self._init_language()

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
                    lambda checked, info=info:
                        info_widget.show(info)
                        if checked else
                        info_widget.hide(info)
                )

    def _connect_language_change(self) -> None:
        def change_language_of_widgets(lang_no: int) -> None:
            new_lang = Language(lang_no)
            for widget in self._window.widgets.values():
                widget.change_language(new_lang)

        def update_language_config(lang_no: int) -> None:
            # Try to reduce the memory comsumption by delete-after-use since
            # language usually aren't changed frequently.
            new_lang = Language(lang_no)
            self._load_language_config()
            self._lang_config["GLOBAL"]["language"] = new_lang.name
            self._store_language_config()
            del self._lang_config

        # index is designed to be as same as the value of enum Language
        self._window.widgets["language"].combox.currentIndexChanged.connect(
            change_language_of_widgets)

        self._window.widgets["language"].combox.currentIndexChanged.connect(
            update_language_config)

    def _connect_grade_output_routines(self) -> None:
        self._json_file: str = to_abs_path("intervals.json")
        parse.init_json(self._json_file)
        self._app.s_concent_interval_refreshed.connect(self._write_grade_into_json)

        self._server_url = f"http://{flask_server.HOST}:{flask_server.PORT}"
        self._app.s_concent_interval_refreshed.connect(self._send_grade_to_server)

    def _send_grade_to_server(self, interval: Interval) -> None:
        # Same as adding keys into __dict__.
        # Surprisingly, this changes the content of __dict__,
        # but doesn't really add attributes to interval.
        interval.time = datetime.fromtimestamp(interval.end).strftime(poster.DATE_STR_FORMAT)
        # TODO: should be changed to a real student id
        interval.id = 100
        try:
            requests.post(self._server_url, json=interval.__dict__)
        except requests.ConnectionError:
            # Skip posting if the connection fails,
            # which may be caused by server not running.
            pass

    def _write_grade_into_json(self, interval: Interval) -> None:
        parse.append_to_json(self._json_file, interval.__dict__)

    def _init_language(self) -> None:
        """Initializes language of window."""
        self._load_language_config()
        self._window.widgets["language"].combox.setCurrentIndex(
            Language[self._lang_config.get("GLOBAL", "language")].value)
        # NOTE: if index changed, self._lang_config is deleted by another method
        if hasattr(self, "_lang_config"):
            del self._lang_config

    def _load_language_config(self) -> None:
        self._lang_config = ConfigParser()
        self._lang_config.read(self._LANGUAGE_CONFIG, encoding="utf-8")

    def _store_language_config(self) -> None:
        with open(self._LANGUAGE_CONFIG, "w", encoding="utf-8") as f:
            self._lang_config.write(f)
