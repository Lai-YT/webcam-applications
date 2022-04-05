import atexit
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from teacher.monitor import ColumnHeader, Monitor, Row
from teacher.worker import ModelWoker
from util.path import to_abs_path


class MonitorController:
    def __init__(self, monitor: Monitor, worker: ModelWoker) -> None:
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

        # Have the connection of database and timer closed right before
        # the controller is destoryed.
        # NOTE: we've tried to listen to the "destoryed" signal of QMainWindow,
        # but such signal seems not guaranteed to always be emitted.
        atexit.register(self._conn.close)

        self._worker = worker
        # notify both database and monitor
        self._worker.s_updated.connect(self.store_new_grade)
        self._worker.s_updated.connect(self.show_new_grade)

    def _connect_database(self) -> None:
        db = Path(to_abs_path("teacher/database/concentration_grade.db"))
        # create database if not exist
        db.parent.mkdir(parents=True, exist_ok=True)
        db.touch()
        self._conn = sqlite3.connect(db, check_same_thread=False, detect_types=sqlite3.PARSE_DECLTYPES)
        # so we can retrieve rows as dictionary
        self._conn.row_factory = sqlite3.Row

    def _create_table_if_not_exist(self) -> None:
        """Creates table if database is empty."""
        TO_SQL_TYPE = {int: "INT", str: "TEXT", float: "FLOAT", datetime: "TIMESTAMP"}

        sql = f"CREATE TABLE IF NOT EXISTS {self._table_name} ("
        for label, value_type in zip(self._monitor.col_header.labels(),
                                     self._monitor.col_header.types()):
            sql += f"{label} {TO_SQL_TYPE[value_type]},"
        sql = sql[:-1] + ");"
        with self._conn:
            self._conn.execute(sql)

    def _fetch_grade(self):
        """Fetches the latest grade from database."""
        with self._conn:
            sql = f"""
                SELECT * FROM {self._table_name} WHERE time=(SELECT MAX(time) FROM {self._table_name})
                ORDER BY id DESC LIMIT 1;
            """
            grade = self._conn.execute(sql).fetchone()
            print(grade)

    def store_new_grade(self, grade: Dict[str, Any]) -> None:
        """Stores new grade into the database."""
        sql = f"INSERT INTO {self._table_name} {self._monitor.col_header.labels()} VALUES (?, ?, ?, ?);"
        row: Row = self._monitor.col_header.to_row(grade)
        with self._conn:
            self._conn.execute(sql, tuple(col.value for col in row))

    def show_new_grade(self, grade: Dict[str, Any]) -> None:
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
