import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication

from teacher.controller import MonitorController
from teacher.monitor import ColumnHeader, Monitor
from teacher.worker import ModelWoker


app = QApplication([])

monitor = Monitor()
worker = ModelWoker()
controller = MonitorController(monitor, worker)
monitor.show()

# 2 workers work concurrently
worker.work()
worker.work()

sys.exit(app.exec_())
