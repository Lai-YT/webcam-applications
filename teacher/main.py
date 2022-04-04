import json
import sys
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from teacher.monitor import ColumnHeader, Monitor


app = QApplication([])
header = ColumnHeader([
    ("status", str),
    ("id", int),
    ("time", int),
    ("grade", float),
])
window = Monitor(header)

data = """[
    {
        "status": "green",
        "id": 1,
        "time": 9991002,
        "grade": 0.85
    },
    {
        "status": "red",
        "id": 2,
        "time": 9991002,
        "grade": 0.67
    },
    {
        "status": "green",
        "id": 3,
        "time": 9991003,
        "grade": 1.0
    },
    {
        "status": "green",
        "id": 4,
        "time": 9991000,
        "grade": 0.9
    }
]"""


for datum in json.loads(data):
    window.insert_row(header.to_row(datum))

window.show()

sys.exit(app.exec_())
