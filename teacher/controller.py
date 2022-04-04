import atexit
import sqlite3

from PyQt5.QtCore import QObject

from teacher.monitor import ColumnHeader, Monitor
from util.path import to_abs_path


class MonitorController(QObject):
    def __init__(self, monitor):
        super().__init__()
        self._monitor = monitor
        self._monitor.col_header = ColumnHeader((
            ("id", int),
            ("time", int),
            ("grade", float),
        ))

        self._connect_database()
        self._table_name = "monitor"
        self._create_table_if_not_exist()

        # Have the connection of database and timer closed right before
        # the controller is destoryed.
        # NOTE: we've tried to listen to the "destoryed" signal of QMainWindow,
        # but such signal seems not guaranteed to always be emitted.
        atexit.register(self._close)

    def _connect_database(self):
        db = to_abs_path("teacher/database/concentration_grade.db")
        self._conn = sqlite3.connect(db, check_same_thread=False)
        # so we can retrieve rows as dictionary
        self._conn.row_factory = sqlite3.Row

    def _create_table_if_not_exist(self) -> None:
        """Creates table if database is empty."""
        TO_SQL_TYPE = {int: "INT", str: "TEXT", float: "FLOAT"}

        sql = f"CREATE TABLE IF NOT EXISTS {self._table_name} ("
        for label, value_type in zip(self._monitor.col_header.labels(),
                                     self._monitor.col_header.types()):
            sql += f"{label} {TO_SQL_TYPE[value_type]},"
        sql = sql[:-1] + ");"
        with self._conn:
            self._conn.execute(sql)

    def insert_new_data(self, data):
        # Insert new data into corresponding table.
        sql = f"INSERT INTO {self._table_name} (id, time, grade) VALUES (?, ?, ?);"
        with self._conn:
            self._conn.execute(sql, (data["id"], data["time"], data["grade"]))
        # Updates to the monitor.
        self._monitor.insert_row(self._monitor.col_header.to_row(data))

    def _close(self):
        self._conn.close()

    @staticmethod
    def _row_not_exists(row: sqlite3.Row) -> bool:
        return row[0] == 0
