import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication

from teacher.controller import MonitorController
from teacher.monitor import ColumnHeader, Monitor


app = QApplication([])

monitor = Monitor(
    ColumnHeader((
        ("id", str),
        ("time", datetime),
        ("grade", float),
    )),
    key_label="id"
)
controller = MonitorController(monitor)
monitor.show()

sys.exit(app.exec_())
