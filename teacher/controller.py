import atexit
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, List, Mapping

import matplotlib.pyplot as plt
import requests
from PyQt5.QtCore import QObject, QTimer, Qt, pyqtSlot
from PyQt5.QtGui import QBrush
from PyQt5.QtWidgets import QTreeWidgetItem

import server.main as flask_server
import server.post as poster
from teacher.monitor import Monitor, RowContent
from util.path import to_abs_path


class MonitorController(QObject):
    TO_SQL_TYPE = {int: "INT", str: "TEXT", float: "FLOAT", datetime: "TIMESTAMP"}

    def __init__(self, monitor: Monitor) -> None:
        super().__init__()
        self._monitor = monitor

        self._connect_database()
        self._table_name = "monitor"
        self._create_table_if_not_exist()
        self._connect_signals()

        self._server_url = f"http://{flask_server.HOST}:{flask_server.PORT}"
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

        Arguments:
            student_id: The id of the student.
            amount: The number of histories to get.
        """
        sql = f"SELECT * FROM {self._table_name} WHERE id=? ORDER BY time DESC LIMIT ?;"
        with self._conn:
            # Fetch one more grade and remove the current one.
            return self._conn.execute(sql, (student_id, amount)).fetchall()

    def store_new_grade(self, grade: Mapping[str, Any]) -> None:
        """Stores new grade into the database."""
        holder = ", ".join(["?"] * self._monitor.col_header.col_count)
        sql = f"INSERT INTO {self._table_name} {tuple(self._monitor.col_header.labels())} VALUES ({holder});"
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
        id_index = self._monitor.col_header.labels().index("id")
        for row in self._get_histories_from_database(student_id, Monitor.MAX_HISTORY_NUM + 1)[1:]:
            hist_item = self._monitor.add_history_of_row(
                row_no, self._monitor.col_header.to_row(row)  # type: ignore
            )  # sqlite3.Row does support mapping
            self._set_background_by_grade(hist_item, row["grade"])

    def _plot_histories(self, student_id: str) -> None:
        grade = []
        time = []
        hist_rows = self._get_histories_from_database(student_id, 6)
        init_time = hist_rows[-1]["time"].timestamp() # earliest grade
        for row in hist_rows:
            grade.append(row["grade"])
            time.append((row["time"].timestamp() - init_time) / 60)
        ax = plt.subplot()
        ax.stem(time, grade)
        ax.set_xlabel("Time from init (minute)")
        ax.set(ylim=(0, 1))
        plt.show()
