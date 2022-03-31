import atexit
import sqlite3
from collections import deque
from pathlib import Path
from typing import Deque

from PyQt5.QtCore import QTimer, QObject, pyqtSlot


class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application
        self._timer = QTimer()
        # the target to fetch grade from
        self._target = "A01"

        self._connect_database()
        self._connect_signal()
        self._clear_table()
        self._start_fetching()

        # Have the connection of database and timer closed right before
        # the controller is destoryed.
        # NOTE: we've tried to listen to the "destoryed" signal of QMainWindow,
        # but such signal seems not guaranteed to always be emitted.
        atexit.register(self._close)

    def _connect_database(self):
        db = Path(__file__).parent / "../concentration_grade.db"
        self._conn = sqlite3.connect(db, check_same_thread=False)
        # so we can retrieve rows as dictionary
        self._conn.row_factory = sqlite3.Row

    def _connect_signal(self):
        input_line = self._gui.input_line
        menu = self._gui.menu

        input_line.textChanged.connect(
            lambda: self._gui.input_line.set_color("black")
        )
        input_line.editingFinished.connect(
            lambda: self._create_table_if_not_exist(input_line.text())
        )
        menu.currentIndexChanged.connect(
            lambda: self._set_target(menu.currentText())
        )

    def _create_table_if_not_exist(self, table) -> None:
        with self._conn:
            # Check if table is already exist.
            tb_exists = "SELECT name FROM sqlite_master WHERE type='table' AND name=?;"

            if not self._conn.execute(tb_exists, (table,)).fetchone():
                # Create new table with name same as input.
                sql = f"""CREATE TABLE {table} (
                    interval TEXT,
                    grade FLOAT
                );"""
                self._conn.execute(sql)
            
                # Add table as an item to the pull-down menu.
                self._gui.menu.addItem(table)
                self._gui.input_line.set_color("green")
                print("Table created successfully")
            else:
                self._gui.input_line.set_color("red")
                print("Table is already exist.")

    def _set_target(self, target: str):
        self._target = target

    def _clear_table(self):
        """Makes sure the tables are empty.

        Since they may contain data from the last connection.
        """
        with self._conn:
            self._conn.execute("DELETE FROM A01;")
            self._conn.execute("DELETE FROM A02;")
            self._conn.execute("DELETE FROM A03;")

    def _start_fetching(self):
        """Fetch grades in database every second."""
        self._timer.timeout.connect(self._fetch_grade_and_update_gui)
        self._timer.start(500)

    def _fetch_grade_and_update_gui(self):
        """Updates the latest grades on GUI."""
        with self._conn:
            # Fetch the three latest grades.
            sql = f"SELECT * FROM {self._target} ORDER BY interval DESC LIMIT 3;"
            grades = self._conn.execute(sql).fetchall()

        if grades:
            title = f"{self._target}: "
            texts: Deque[str] = deque()
            for grade in grades:
                # Append the grade in front to keep grades in order by interval.
                texts.appendleft(f"{grade['interval']} {grade['grade']}")
            self._gui.label.setText(title + "\n" + "\n".join(texts))

    def update_grade_in_database(self, grade):
        # Insert new grade into corresponding table.
        with self._conn:
            sql = f"INSERT INTO {grade['id']} (interval, grade) VALUES (?, ?);"
            self._conn.execute(
                sql, (grade["interval"], grade["grade"])
            )

    def _close(self):
        self._conn.close()
        self._timer.stop()

    @staticmethod
    def _row_not_exists(row: sqlite3.Row) -> bool:
        return row[0] == 0
