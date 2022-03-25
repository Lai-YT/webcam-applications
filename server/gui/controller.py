import atexit
import sqlite3
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot


class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application
        self._grade = None

        self._connect_database()
        self._clear_table()

        atexit.register(self._conn.close)

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

    def _clear_table(self):
        with self._conn:
            self._conn.execute("DELETE FROM grades;")   

    def update_grade_in_database(self, grade):
        self._grade = grade

        with self._conn:
            sql = "SELECT EXISTS (SELECT 1 FROM grades WHERE id=? LIMIT 1);"
            row = self._conn.execute(sql, (self._grade["id"], )).fetchone()
            # row not exists
            if row[0] == 0:
                sql = "INSERT INTO grades (id, interval, grade) VALUES (?, ?, ?);"
                self._conn.execute(
                    sql, (self._grade["id"], self._grade["interval"], self._grade["grade"])
                )
            # row exists
            else:
                sql = "UPDATE grades SET interval=?, grade=? WHERE id=?;"
                self._conn.execute(
                    sql, (self._grade["interval"], self._grade["grade"], self._grade["id"])
                )

    def _update_grade_on_gui(self):
        """Updates the latest grade of "A01" to the GUI."""
        with self._conn:
            sql = """SELECT interval, grade FROM grades WHERE id="A01";"""
            rows = self._conn.execute(sql).fetchall()
        text = "A01: \n"
        for row in rows[-1:]:
            text += "    {} {}\n".format(row["interval"], row["grade"])
        self._gui.label.setText(text)
