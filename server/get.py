import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication
import requests

import server.main as flask_server
import server.post as poster
from teacher.controller import MonitorController
from teacher.monitor import ColumnHeader, Monitor


r = requests.get(f"http://{flask_server.HOST}:{flask_server.PORT}/grade")

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


for datum in r.json():
    # Convert time string to datetime.
    datum["time"] = datetime.strptime(datum["time"], poster.DATE_STR_FORMAT)

    controller.store_new_grade(datum)
    controller.show_new_grade(datum)


sys.exit(app.exec_())
