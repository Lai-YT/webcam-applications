import atexit
import sqlite3
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot


class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application

        self._connect_database()
        self._create_table_if_not_exists()
        self._clear_table()

        # Have the connection of database closed right before
        # the controller is destoryed.
        # NOTE: we've tried to listen to the "destoryed" signal of QMainWindow,
        # but such signal seems not guaranteed to always be emitted.
        atexit.register(self._conn.close)

    def _connect_database(self):
        db = Path(__file__).parent / "../concentration_grade.db"
        self._conn = sqlite3.connect(db, check_same_thread=False)
        # so we can retrieve rows as dictionary
        self._conn.row_factory = sqlite3.Row

    def _create_table_if_not_exists(self) -> None:
        # TODO: make student id the primary key
        with self._conn:
            sql = """CREATE TABLE IF NOT EXISTS grades (
                id INT,
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

    def update_grade_in_database(self, grade):
        # Checks whether the id already exists,
        # if yes, UPDATEs its content;
        # if no, INSERTs as a new row.
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
        # TODO: update the grade periodically
        self._update_grade_on_gui()

    def _update_grade_on_gui(self):
        """Updates the latest grade of "A01" to the GUI."""
        with self._conn:
            sql = 'SELECT interval, grade FROM grades WHERE id="A01" LIMIT 1;'
            row = self._conn.execute(sql).fetchone()
        text = "A01: \n"
        text += "    {} {}\n".format(row["interval"], row["grade"])
        self._gui.label.setText(text)

    @staticmethod
    def _row_not_exists(row: sqlite3.Row) -> bool:
        return row[0] == 0
