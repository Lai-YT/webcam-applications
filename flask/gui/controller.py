import sqlite3
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot


class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application
        self._grade = None

        self._connect_signal()
        self._connect_database()

    def _connect_signal(self):
        self._gui.destroyed.connect(self._clear_table)

    def _connect_database(self):
        db = Path(__file__).parent / "../concentration_grade.db"
        self._conn = sqlite3.connect(db, check_same_thread=False)
        # so we can retrieve rows as dictionary
        self._conn.row_factory = sqlite3.Row
        with self._conn:
            sql = """CREATE TABLE IF NOT EXISTS grades (
                id INT,
                interval TEXT,
                grade FLOAT
            );"""
            self._conn.execute(sql)

    def store_grade_in_database(self, grade):
        self._grade = grade

        with self._conn:
            sql = "INSERT INTO grades (id, interval, grade) VALUES (?, ?, ?);"
            self._conn.execute(
                sql, (self._grade["id"], self._grade["interval"], self._grade["grade"])
            )
        self._update_grade_on_gui()

    def _update_grade_on_gui(self):
        """Updates the latest grade of "A01" to the GUI."""
        with self._conn:
            sql = """SELECT interval, grade FROM grades WHERE id="A01";"""
            rows = self._conn.execute(sql).fetchall()
        text = "A01: \n"
        for row in rows[-1]:
            text += "    {} {}\n".format(row["interval"], row["grade"])
        self._gui.label.setText(text)

    @pyqtSlot()
    def _clear_table(self):
        # XXX: is the table always deleted?
        with self._conn:
            self._conn.execute("DELETE FROM grades;")
        self._conn.close()
