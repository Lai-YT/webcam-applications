import sqlite3

from PyQt5.QtCore import QObject, pyqtSlot

class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application

        self._connect_siganl()
        self._connect_database()

    def _connect_siganl(self):
        self._gui.destroyed.connect(self._clear_table)

    def _connect_database(self):
        grades = "concentration_grade.db"
        self.conn = sqlite3.connect(grades, check_same_thread=False)

    def store_grade(self, grade):
        sql_str = ("insert into grades(id, interval, grade) values('{}','{}',{});"
            .format(grade["id"], grade["interval"], grade["grade"])
        )
        self.conn.execute(sql_str)
        self.conn.commit()

    def update_grade(self):
        pass

    @pyqtSlot()
    def _clear_table(self):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM grades")
        self.conn.commit()
        self.conn.close()
