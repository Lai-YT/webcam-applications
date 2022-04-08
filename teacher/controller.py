import atexit
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, List, Mapping

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from teacher.monitor import ColumnHeader, Monitor, Row
from teacher.worker import ModelWoker
from util.path import to_abs_path
from util.task_worker import TaskWorker


class MonitorController(QObject):
    s_showed = pyqtSignal(sqlite3.Row)

    TO_SQL_TYPE = {int: "INT", str: "TEXT", float: "FLOAT", datetime: "TIMESTAMP"}

    def __init__(self, monitor: Monitor, worker: ModelWoker) -> None:
        super().__init__()
        self._monitor = monitor
        self._monitor.col_header = ColumnHeader((
            ("status", str),
            ("id", int),
            ("time", datetime),
            ("grade", float),
        ))

        self._connect_database()
        self._table_name = "monitor"
        self._create_table_if_not_exist()
        self._connect_signal()
        self._fetch_grades_and_show()

        # Have the connection of database and timer closed right before
        # the controller is destoryed.
        # NOTE: we've tried to listen to the "destoryed" signal of QMainWindow,
        # but such signal seems not guaranteed to always be emitted.
        atexit.register(self._conn.close)

        # Currently testing the "fetch" operation, so worker is ignored.
        # self._worker = worker

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

    def _connect_signal(self) -> None:
        self.s_showed.connect(self.show_new_grade)

    def _fetch_grades_and_show(self) -> None:
        """Fetches grades from database and passes to monitor one by one."""
        grades = self._fetch_grades_from_database()
        self._worker = TaskWorker(self._show_grades_one_by_one, grades)
        self._worker.start()

    def _fetch_grades_from_database(self) -> List[sqlite3.Row]:
        """Fetches all grades from database."""
        with self._conn:
            sql = f"SELECT * FROM {self._table_name} ORDER BY time;"
            grades = self._conn.execute(sql).fetchall()
        return grades

    def _show_grades_one_by_one(self, grades: List[sqlite3.Row]) -> None:
        for grade in grades:
            self.s_showed.emit(grade)
            time.sleep(1)

    def store_new_grade(self, grade: Mapping[str, Any]) -> None:
        """Stores new grade into the database."""
        sql = f"INSERT INTO {self._table_name} {self._monitor.col_header.labels()} VALUES (?, ?, ?, ?);"
        row: Row = self._monitor.col_header.to_row(grade)
        with self._conn:
            self._conn.execute(sql, tuple(col.value for col in row))

    @pyqtSlot(dict)
    def show_new_grade(self, grade: Mapping[str, Any]) -> None:
        """Shows the new grade to the monitor.

        A new row is inserted if the "id" introduces a new student,
        otherwise the students grade is updated to the same row.
        """
        row_no = self._monitor.search_row_no(("id", grade["id"]))
        row: Row = self._monitor.col_header.to_row(grade)
        if row_no == -1:  # row not found
            self._monitor.insert_row(row)
        else:
            self._monitor.update_row(row_no, row)

    @staticmethod
    def _row_not_exists(row: sqlite3.Row) -> bool:
        return row[0] == 0
