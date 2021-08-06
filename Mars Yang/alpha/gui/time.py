import sys
import os
cwd: str = os.path.abspath(__file__)
rel: str = "../../lib"
sys.path.append(os.path.abspath(os.path.join(cwd, rel)))

from PyQt5 import QtCore, QtWidgets

import gui.time_ui as time_ui
from lib.timer import Timer


class TimeWindow(QtWidgets.QMainWindow, time_ui.Ui_MainWindow):
    def __init__(self, timer: Timer) -> None:
        super().__init__()
        self.setupUi(self)
        self._timer = timer

    def update_time(self) -> None:
        time: str = f"{self._timer.time()//60:02d}:{self._timer.time()%60:02d}"
        self.lcdNumber.display(time)

    @property
    def timer(self) -> Timer:
        return self._timer


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    timer = Timer()
    timer.start()
    window = TimeWindow(timer)
    window.show()
    window.update_time()
    sys.exit(app.exec_())
