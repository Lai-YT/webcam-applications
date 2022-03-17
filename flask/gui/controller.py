from PyQt5.QtCore import QObject


class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application

    def update_grade(self, grade):
        id = grade["id"]
        time = grade["interval"]
        grade = grade["grade"]

        text = f"Student {id}\nTime: {time}\nGrade: {grade}"
        self._gui.label.setText(text)
