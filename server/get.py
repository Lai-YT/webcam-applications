import requests
import sys
from datetime import datetime 

from PyQt5.QtWidgets import QApplication

from teacher.controller import MonitorController
from teacher.monitor import Monitor

r = requests.get("http://127.0.0.1:5000/")
# print(r.status_code)
# print(r.headers)

app = QApplication([])
monitor = Monitor()
controller = MonitorController(monitor)
monitor.show()

for data in r.json():
    # Convert time string to datetime.
    time = datetime.strptime(data["time"], "%Y-%m-%d, %H:%M:%S")
    data["time"] = time
    # Add grade status in data.
    status = "red" if data["grade"] < 0.8 else "green"
    data.update({"status": status})

    controller.store_new_grade(data)
    controller.show_new_grade(data)

sys.exit(app.exec_())
