import sys
from datetime import datetime

from PyQt5.QtWidgets import QApplication

from teacher.monitor import ColumnHeader, Monitor


app = QApplication([])
window = Monitor(ColumnHeader([
    ("status", str),
    ("id", int),
    ("time", datetime),
    ("grade", float),
]))

data = [
    {
        "status": "green",
        "id": 1,
        "time": datetime.fromisoformat("2022-04-04 19:05:23"),
        "grade": 0.9
    },
    {
        "status": "red",
        "id": 2,
        "time": datetime.fromisoformat("2022-04-04 19:05:24"),
        "grade": 0.67
    },
    {
        "status": "green",
        "id": 3,
        "time": datetime.fromisoformat("2022-04-04 19:05:23"),
        "grade": 1.0
    },
    {
        "status": "green",
        "id": 4,
        "time": datetime.fromisoformat("2022-04-04 19:05:22"),
        "grade": 0.9
    }
]

for datum in data:
    window.insert_row(window.col_header.to_row(datum))

window.show()

sys.exit(app.exec_())
