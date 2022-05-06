import atexit
import math
import sqlite3
import time
from configparser import ConfigParser
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Mapping

import matplotlib.pyplot as plt
import numpy as np
import requests
from PyQt5.QtCore import QObject, QTimer, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QTreeWidgetItem

import server.main as flask_server
import server.post as poster
from gui.language import Language
from screenshot.compare import (
    compare_similarity_of_slices, get_compare_slices, get_screenshot
)
from teacher.monitor import Col, Monitor, RowContent
from util.path import to_abs_path
from util.task_worker import TaskWorker
from util.time import to_date_time


class MonitorController(QObject):
    """Data logic, server communitcation and database managemnt are mixed into
    the controller for simplicity.
    """

    # private signal for thread communitcation;
    # sends the student id with the similarity of screenshot slice
    _s_screen_similarity_refreshed = pyqtSignal(str, float)

    def __init__(self, monitor: Monitor) -> None:
        super().__init__()
        self._monitor = monitor

        self._connect_database()
        self._table_name = "monitor"
        self._create_table_if_not_exist()
        self._connect_signals()

        self._server_url = f"https://c4e073bfe7648e.lhrtunnel.link"
        self._fetch_timer = QTimer()
        self._fetch_timer.timeout.connect(self._get_grades_from_server)
        self._fetch_timer.start(30 * 1000) # 30 sec

        self._screenshot_worker = TaskWorker(self._get_screenshot_slices_periodically)
        self._compare_worker = TaskWorker(self._compare_screenshot_similarity_periodically)
        self._screenshot_worker.start()
        self._compare_worker.start()

        self._CONFIG_FILE = to_abs_path("./teacher/config.ini")
        self._init_global_config()
        atexit.register(self._store_global_config)

        # Have the connection of database and timer closed right before
        # the controller is destoryed.
        # NOTE: we've tried to listen to the "destoryed" signal of QMainWindow,
        # but such signal seems not guaranteed to always be emitted.
        atexit.register(self._conn.close)

    def _connect_database(self) -> None:
        db = Path(to_abs_path("teacher/database/concentration_grade.db"))
        # create database if not exist
        db.parent.mkdir(parents=True, exist_ok=True)
        db.touch()
        # PARSE_DECLTYPES so TIMESTAMP may be converted back to datetime
        self._conn = sqlite3.connect(db, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
        # so we can retrieve rows as dictionary
        self._conn.row_factory = sqlite3.Row

    def _create_table_if_not_exist(self) -> None:
        """Creates table if database is empty."""
        sql = f"""CREATE TABLE IF NOT EXISTS {self._table_name} (
            id TEXT,
            time TIMESTAMP,
            grade FLOAT
        );"""
        with self._conn:
            self._conn.execute(sql)

    def _connect_signals(self):
        self._monitor.s_item_clicked.connect(
            lambda student_id, label: self._plot_histories(student_id)
                                      if label == "grade" else None
        )
        self._monitor.s_item_collapsed.connect(
            lambda student_id: self._monitor.remove_histories_of_row(
                self._monitor.search_row_no(("id", student_id))
            )
        )
        self._monitor.s_item_expanded.connect(self._show_histories_on_monitor)
        self._s_screen_similarity_refreshed.connect(self._show_similarity_of_screenshot_to_monitor)
        # index is designed to be as same as the value of enum Language
        self._monitor.combox.currentIndexChanged.connect(self._change_language_of_monitor)

    def _get_grades_from_server(self) -> None:
        """Get new grades from the server and
        (1) stores into the database (2) updates to the GUI.
        """
        r = requests.get(f"{self._server_url}/grade")
        for datum in r.json():
            # Convert time string to datetime.
            datum["time"] = datetime.strptime(datum["time"], poster.DATE_STR_FORMAT)

            self.store_new_grade(datum)
            self.show_new_grade(datum)

    def _get_histories_from_database(self, student_id: str, amount: int) -> List[sqlite3.Row]:
        """Gets latest histories of the student specified by id from the database.

        Histories are in descending order with repect to their time.

        Arguments:
            student_id: The id of the student.
            amount: The number of histories to get.
        """
        sql = f"SELECT * FROM {self._table_name} WHERE id=? ORDER BY time DESC LIMIT ?;"
        with self._conn:
            return self._conn.execute(sql, (student_id, amount)).fetchall()

    def store_new_grade(self, grade: Mapping[str, Any]) -> None:
        """Stores new grade into the database."""
        sql = f"INSERT INTO {self._table_name} (id, time, grade) VALUES (?, ?, ?);"
        row: RowContent = self._monitor.col_header.to_row(grade)
        with self._conn:
            self._conn.execute(sql, tuple(col.value for col in row))

    def show_new_grade(self, grade: Mapping[str, Any]) -> None:
        """Shows the new grade to the monitor and sorts rows in ascending order
        with respect to label "grade".

        A new row is inserted if the "id" introduces a new student,
        otherwise the student's grade is updated to the original row.
        """
        row_no = self._monitor.search_row_no(("id", grade["id"]))
        row: RowContent = self._monitor.col_header.to_row(grade)
        if row_no == -1:  # row not found
            row_item = self._monitor.insert_row(row)
        else:
            row_item = self._monitor.update_row(row_no, row)
        self._monitor.sort_rows_by_label("grade", Qt.AscendingOrder)
        self._set_background_by_grade(row_item, grade["grade"])

        # FIXME: method call on private attribute
        for i in range(self._monitor._table.topLevelItemCount()):
            item = self._monitor._table.topLevelItem(i)
            # Search all expanded items and refresh histories.
            if item.isExpanded():
                self._monitor.remove_histories_of_row(i)
                self._show_histories_on_monitor(
                    item.text(self._monitor.col_header.labels().index("id"))
                )

    def _set_background_by_grade(self, row_item: QTreeWidgetItem, grade: float) -> None:
        """Sets the background of label "grade" to green if grade is higher than
        0.8, else to red.

        Which implies the status of the specific student.
        """
        color: Qt.GlobalColor = Qt.green
        if grade < 0.8:
            color = Qt.red
        col_no = self._monitor.col_header.labels().index("grade")
        row_item.setBackground(col_no, QBrush(color, Qt.Dense4Pattern))

    @pyqtSlot(str)
    def _show_histories_on_monitor(self, student_id: str) -> None:
        """Shows Monitor.MAX_HISTORY_NUM latest histories of the student
        specified by id on the monitor.
        """
        row_no = self._monitor.search_row_no(("id", student_id))
        # Fetch one more grade and remove the current one.
        for row in self._get_histories_from_database(student_id, Monitor.MAX_HISTORY_NUM + 1)[1:]:
            hist_item = self._monitor.add_history_of_row(
                row_no, self._monitor.col_header.to_row(row)  # type: ignore
            )  # sqlite3.Row does support mapping
            self._set_background_by_grade(hist_item, row["grade"])

    def _plot_histories(self, student_id: str) -> None:
        """Plots at most 50 histories of the latest 50 minutes."""
        # We assume that a single course takes 50 minutes, so at most 50
        # histories will be plotted and history farther than 50 minutes from now
        # will be ignored.
        histories: List[sqlite3.Row] = list(filter(
            lambda row: row["time"] > datetime.now() - timedelta(minutes=50),
            self._get_histories_from_database(student_id, 50)
        ))
        time_of_earliest_grade: int = histories[-1]["time"].timestamp()
        grades: List[float] = []
        times: List[float] = []
        for row in histories:
            grades.append(row["grade"])
            # convert to min
            times.append(1 + (row["time"].timestamp() - time_of_earliest_grade) / 60)
        ax = plt.subplot()
        ax.plot(times, grades)
        ax.set_title(f"Concentration grade of id: {student_id} from {to_date_time(time_of_earliest_grade)}")
        ax.set_ylabel("grade")
        ax.set_xlabel("time (min)")
        ax.set_xticks(range(math.ceil(times[0]) + 1))
        # show the real "stop" point by showing "stop + step"
        ax.set_yticks(np.arange(0, 1 + 0.2, 0.2))
        ax.set_yticks(np.arange(0.1, 0.9 + 0.2, 0.2), minor=True)
        ax.set_ylim(0, 1.1)  # more than 1 so not truncate the circle on the top
        plt.show()

    def _get_screenshot_slices_from_server(self) -> Dict:
        r = requests.get(f"{self._server_url}/screenshot")
        return r.json()

    def _get_screenshot_slices_periodically(self) -> None:
        now = datetime.now()
        minute = (now.minute // 5) * 5
        next_fire = now.replace(minute=minute, second=0, microsecond=0) + timedelta(minutes=5)
        BUSY_CHECK_GAP = 2
        sleep = (next_fire - now).seconds

        while True:
            time.sleep(sleep)
            while datetime.now() < next_fire:
                pass
            self._screenshot_slices = get_compare_slices(get_screenshot())

            next_fire += timedelta(minutes=5)
            sleep = 5 * 60 - BUSY_CHECK_GAP

    def _compare_screenshot_similarity(self) -> None:
        """Compares the slices of students with teacher's."""
        for data in self._get_screenshot_slices_from_server():
            slices = data["slices"]
            similarity: float = compare_similarity_of_slices(
                np.array(slices), self._screenshot_slices
            )
            self._s_screen_similarity_refreshed.emit(data["id"], similarity)

    @pyqtSlot(str, float)
    def _show_similarity_of_screenshot_to_monitor(self, student_id: str, similarity: float) -> None:
        """Shows the similarity of screen to the corresponding student's screen label."""
        row_no = self._monitor.search_row_no(("id", student_id))
        row = RowContent([Col(no=self._monitor.col_header.labels().index("screen"),
                              label="screen",
                              # round to 2 decimal places
                              value=Decimal(f"{similarity:.2f}"))])
        if row_no == -1:  # row not found
            row_item = self._monitor.insert_row(row)
        else:
            row_item = self._monitor.update_row(row_no, row)
        color: Qt.GlobalColor = Qt.green
        if similarity < 0.6:
            color = Qt.red
        col_no = self._monitor.col_header.labels().index("screen")
        row_item.setBackground(col_no, QBrush(color, Qt.Dense4Pattern))

    def _compare_screenshot_similarity_periodically(self) -> None:
        now = datetime.now()
        # generate a time offset to make sure screenshot are gotten
        minute = (now.minute // 5) * 5 + 1
        next_fire = (
            now.replace(minute=minute, second=0, microsecond=0)
            + timedelta(minutes=5 * 2)  # an extra delta to make sure the 1st screenshot of teacher is gotten
        )
        BUSY_CHECK_GAP = 2
        sleep = (next_fire - now).seconds

        while True:
            time.sleep(sleep)
            while datetime.now() < next_fire:
                pass
            self._compare_screenshot_similarity()

            next_fire += timedelta(minutes=5)
            sleep = 5 * 60 - BUSY_CHECK_GAP

    def _change_language_of_monitor(self, lang_no: int) -> None:
        self._lang = Language(lang_no)
        self._monitor.change_language(self._lang)

    def _init_global_config(self) -> None:
        """Initializes the language of window."""
        # Try to reduce the memory comsumption by delete-after-use.
        self._load_global_config()
        self._lang = Language[self._config.get("GLOBAL", "language")]
        del self._config

        self._monitor.combox.setCurrentIndex(self._lang.value)

    def _load_global_config(self) -> None:
        self._config = ConfigParser()
        self._config.read(self._CONFIG_FILE, encoding="utf-8")

    def _store_global_config(self) -> None:
        """Writes the current global configurations back into the config file."""
        self._load_global_config()

        self._config["GLOBAL"]["language"] = self._lang.name

        with open(self._CONFIG_FILE, "w", encoding="utf-8") as f:
            self._config.write(f)
