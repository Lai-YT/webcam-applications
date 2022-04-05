import atexit
import sqlite3
from datetime import datetime
from typing import Any, Dict


from teacher.monitor import ColumnHeader, Monitor
from util.path import to_abs_path


class MonitorController:
    def __init__(self, monitor: Monitor) -> None:
        super().__init__()
        self._monitor = monitor
        self._monitor.col_header = ColumnHeader((
            ("id", int),
            ("time", str),
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

    def _connect_database(self) -> None:
        db = to_abs_path("teacher/database/concentration_grade.db")
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

    def send_new_data(self, data: Dict[str, Any]) -> None:
        # Insert new data into corresponding table.
        sql = f"INSERT INTO {self._table_name} (id, time, grade) VALUES (?, ?, ?);"
        with self._conn:
            self._conn.execute(sql, (data["id"], data["time"], data["grade"]))
        # Updates to the monitor.
        row_no = self._monitor.search_row_no(("id", data["id"]))
        row: Row = self._monitor.col_header.to_row(data)
        if row_no == -1:
            self._monitor.insert_row(row)
        else:
            print("update", ("id", data["id"]))
            self._monitor.update_row(row_no, row)

    def _close(self):
        self._conn.close()

    @staticmethod
    def _row_not_exists(row: sqlite3.Row) -> bool:
        return row[0] == 0
