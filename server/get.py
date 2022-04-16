import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication
import requests

import server.main as flask_server
import server.post as poster
from teacher.controller import MonitorController
from teacher.monitor import ColumnHeader, Monitor


r = requests.get(f"http://{flask_server.HOST}:{flask_server.PORT}/")

app = QApplication([])
monitor = Monitor(
    ColumnHeader((
        ("status", str),
        ("id", int),
        ("time", datetime),
        ("grade", float),
    )),
    key_label="id"
)
controller = MonitorController(monitor)
monitor.show()


for datum in r.json():
    # Convert time string to datetime.
    datum["time"] = datetime.strptime(datum["time"], poster.DATE_STR_FORMAT)
    # Add grade status in data.
    datum["status"] = "X" if datum["grade"] < 0.8 else "O"

    controller.store_new_grade(datum)
    controller.show_new_grade(datum)


sys.exit(app.exec_())
