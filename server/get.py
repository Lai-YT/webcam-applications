import requests
import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication

import server.main as flask_server
import server.post as poster
from teacher.controller import MonitorController
from teacher.monitor import Monitor


r = requests.get(f"http://{flask_server.HOST}:{flask_server.PORT}/")

app = QApplication([])
monitor = Monitor()
controller = MonitorController(monitor)
monitor.show()


for data in r.json():
    # Convert time string to datetime.
    data["time"] = datetime.strptime(data["time"], poster.DATE_STR_FORMAT)
    # Add grade status in data.
    data["status"] = "red" if data["grade"] < 0.8 else "green"

    controller.store_new_grade(data)
    controller.show_new_grade(data)


sys.exit(app.exec_())
