import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication

from teacher.controller import MonitorController
from teacher.monitor import Monitor


app = QApplication([])

monitor = Monitor()
controller = MonitorController(monitor)
monitor.show()

sys.exit(app.exec_())
