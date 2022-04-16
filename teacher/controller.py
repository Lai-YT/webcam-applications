import atexit
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

import requests
from PyQt5.QtCore import QObject, QTimer, Qt

import server.main as flask_server
import server.post as poster
from teacher.monitor import Monitor, Row
from util.path import to_abs_path


class MonitorController(QObject):
    TO_SQL_TYPE = {int: "INT", str: "TEXT", float: "FLOAT", datetime: "TIMESTAMP"}

    def __init__(self, monitor: Monitor) -> None:
        super().__init__()
        self._monitor = monitor

        self._connect_database()
        self._table_name = "monitor"
        self._create_table_if_not_exist()
        self._connect_signal()

        self._server_url = f"http://{flask_server.HOST}:{flask_server.PORT}/"
        self._fetch_timer = QTimer()
        self._fetch_timer.timeout.connect(self._get_grades_from_server)
        self._fetch_timer.start(1000)

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
        sql = f"CREATE TABLE IF NOT EXISTS {self._table_name} ("
        for label, value_type in zip(self._monitor.col_header.labels(),
                                     self._monitor.col_header.types()):
            sql += f"{label} {MonitorController.TO_SQL_TYPE[value_type]},"
        sql = sql[:-1] + ");"
        with self._conn:
            self._conn.execute(sql)

    def _connect_signal(self):
        self._monitor.s_button_clicked.connect(lambda id: print(id))

    def _get_grades_from_server(self) -> None:
        """Get new grades from the server and
        (1) stores into the database (2) updates to the GUI.
        """
        r = requests.get(self._server_url)
        for datum in r.json():
            # Convert time string to datetime.
            datum["time"] = datetime.strptime(datum["time"], poster.DATE_STR_FORMAT)
            # Add grade status in data.
            datum["status"] = "X" if datum["grade"] < 0.8 else "O"

            self.store_new_grade(datum)
            self.show_new_grade(datum)

    def store_new_grade(self, grade: Mapping[str, Any]) -> None:
        """Stores new grade into the database."""
        sql = f"INSERT INTO {self._table_name} {self._monitor.col_header.labels()} VALUES (?, ?, ?, ?);"
        row: Row = self._monitor.col_header.to_row(grade)
        with self._conn:
            self._conn.execute(sql, tuple(col.value for col in row))

    def show_new_grade(self, grade: Mapping[str, Any]) -> None:
        """Shows the new grade to the monitor and sorts rows in ascending order
        with respect to label "grade".

        A new row is inserted if the "id" introduces a new student,
        otherwise the students grade is updated to the original row.
        """
        row_no = self._monitor.search_row_no(("id", grade["id"]))
        row: Row = self._monitor.col_header.to_row(grade)
        if row_no == -1:  # row not found
            self._monitor.insert_row(row)
        else:
            self._monitor.update_row(row_no, row)
        self._monitor.sort_rows_by_label("grade", Qt.AscendingOrder)

    @staticmethod
    def _row_not_exists(row: sqlite3.Row) -> bool:
        return row[0] == 0
