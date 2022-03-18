from PyQt5.QtCore import QObject


class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application

    def update_grade(self, grade):
        text = "Student {}\nTime: {}\nGrade: {}".format(
            grade["id"], grade["interval"], grade["grade"])
        self._gui.label.setText(text)
