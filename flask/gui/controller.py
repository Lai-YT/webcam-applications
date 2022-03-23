import sqlite3
from pathlib import Path

from PyQt5.QtCore import QObject, pyqtSlot


class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application

        self._connect_signal()
        self._connect_database()

    def _connect_signal(self):
        self._gui.destroyed.connect(self._clear_table)

    def _connect_database(self):
        db = Path(__file__).parent / "../concentration_grade.db"
        self._conn = sqlite3.connect(db, check_same_thread=False)

    def store_grade(self, grade):
        sql = "INSERT INTO grades (id, interval, grade) VALUES (?, ?, ?);"
        with self._conn:
            self._conn.execute(sql, (grade["id"], grade["interval"], grade["grade"]))

    def update_grade(self):
        pass

    @pyqtSlot()
    def _clear_table(self):
        with self._conn:
            self._conn.execute("DELETE FROM grades;")
        self._conn.close()
