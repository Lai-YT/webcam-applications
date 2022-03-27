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
        self._counter = 0

        self._connect_database()
        self._create_table_if_not_exist()
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

    def _create_table_if_not_exist(self) -> None:
        # TODO: make student id the primary key
        with self._conn:
            sql = """CREATE TABLE IF NOT EXISTS grades (
                id INT PRIMARY KEY,
                interval TEXT,
                grade FLOAT
            );"""
            self._conn.execute(sql)

    def _clear_table(self):
        """Makes sure the table is empty.

        Since it may contains data from the last connection.
        """
        with self._conn:
            self._conn.execute("DELETE FROM grades;")

    def _start_fetching(self):
        """Fetch grades in database every second."""
        self._timer.timeout.connect(self._fetch_grade_and_update_gui)
        self._timer.start(1000)

    def update_grade_in_database(self, grade):
        # Checks whether the id already exists,
        # if yes, UPDATE its content;
        # if no, INSERT as a new row.
        with self._conn:
            sql = "SELECT EXISTS (SELECT 1 FROM grades WHERE id=? LIMIT 1);"
            row = self._conn.execute(sql, (grade["id"], )).fetchone()

            if self._row_not_exists(row):
                sql = "INSERT INTO grades (interval, grade, id) VALUES (?, ?, ?);"
            else:
                sql = "UPDATE grades SET interval=?, grade=? WHERE id=?;"
            # notice the order of columns should be the same
            self._conn.execute(
                sql, (grade["interval"], grade["grade"], grade["id"])
            )

    def _fetch_grade_and_update_gui(self):
        """Updates the latest grades on GUI."""
        with self._conn:
            sql = "SELECT * FROM grades;"
            rows = self._conn.execute(sql).fetchall()

        self._counter = self._counter + 1
        text = "Fetch time: {}\n".format(self._counter)
        for row in rows:
            text += "{}: \n{} {}\n".format(row["id"], row["interval"], row["grade"])
        self._gui.label.setText(text)

    def _close(self):
        self._conn.close()
        self._timer.stop()

    @staticmethod
    def _row_not_exists(row: sqlite3.Row) -> bool:
        return row[0] == 0
