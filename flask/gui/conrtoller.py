from PyQt5.QtCore import QObject, pyqtSlot

class GuiController(QObject):
    def __init__(self, gui, application):
        super().__init__()
        self._gui = gui
        self._app = application

        self._counter = 0

    def update_counter(self, data_list):
        self._counter = self._counter + 1
        self._gui.label.setText(str(data_list))
