import atexit
import sqlite3
from pathlib import Path

from PyQt5.QtCore import QTimer, QObject, pyqtSlot


class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application
        self._timer = QTimer()

        self._connect_database()
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
        # Create table if database is empty.
        self._create_table_if_not_exist()
        self._clear_table()

    def _create_table_if_not_exist(self) -> None:
        with self._conn:
            sql = """CREATE TABLE IF NOT EXISTS grades (
                id INT,
                time TEXT,
                grade FLOAT
            );"""
            self._conn.execute(sql)

    def _clear_table(self):
        """Makes sure the table is empty.

        Since it may contain data from the last connection.
        """
        with self._conn:
            self._conn.execute("DELETE FROM grades;")

    def _start_fetching(self):
        """Fetch grades in database every second."""
        self._timer.timeout.connect(self._fetch_grade_and_update_gui)
        self._timer.start(500)

    def _fetch_grade_and_update_gui(self):
        """Updates the latest grades on GUI."""
        with self._conn:
            sql = (
                "SELECT * FROM grades WHERE time = (SELECT MAX(time) FROM grades) "
                "ORDER BY id DESC LIMIT 1;"
            )
            grade = self._conn.execute(sql).fetchone()

        if grade:
            print("{} {} {}".format(grade["id"], grade["time"], grade["grade"]))
            if grade["grade"] >= 0.6:
                color = "green"
            else:
                color = "red"
        
            self._gui.label.setText(grade["id"])
            self._gui.label.set_color(color)

    def insert_grade_in_database(self, grade):
        # Insert new grade into corresponding table.
        with self._conn:
            sql = f"INSERT INTO grades (id, time, grade) VALUES (?, ?, ?);"
            self._conn.execute(
                sql, (grade['id'], grade["time"], grade["grade"])
            )

    def _close(self):
        self._conn.close()
        self._timer.stop()

    @staticmethod
    def _row_not_exists(row: sqlite3.Row) -> bool:
        return row[0] == 0
