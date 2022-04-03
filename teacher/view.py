import sys
import sqlite3
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QTableWidget, QTableWidgetItem, QMainWindow


app = QApplication([])

window = QMainWindow()
window.setWindowTitle("Teacher Monitor")

LABELS = ("status", "id", "time", "grade")
NUM_OF_STU = 5
table = QTableWidget(NUM_OF_STU, len(LABELS))
window.setCentralWidget(table)

table.setHorizontalHeaderLabels(LABELS)

data = {
    "status": "green",
    "id": 1,
    "time": 9991002,
    "grade": 0.85,
}

table.insertRow(table.rowCount())
for col_label, value in data.items():
    table.setItem(table.rowCount() - 1, LABELS.index(col_label), QTableWidgetItem(str(value)))

window.resize(640, 480)
window.show()

sys.exit(app.exec_())
