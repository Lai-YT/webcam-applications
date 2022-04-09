"""This is a model worker which simulates the behavior from Student-end.
Posts grades to the server.
"""

import sys
import time
from datetime import datetime
from random import randint, shuffle
from typing import Dict, List

import requests
from PyQt5.QtWidgets import QApplication

import server.main as flask_server
from util.task_worker import TaskWorker


class ModelWoker:
    def __init__(self) -> None:
        super().__init__()
        self._workers: List[TaskWorker] = []

    def work(self) -> None:
        """A new worker thread is generated each time this method is called."""
        worker = TaskWorker(self._send_grades)
        self._workers.append(worker)
        worker.start()

    def _send_grades(self) -> None:
        """This is the main loop which sends new grades periodically."""

        student_ids = [1, 2, 3, 4]
        shuffle(student_ids)

        for student_id in student_ids:
            time.sleep(randint(1, 3))
            grade = ModelWoker._generate_real_time_random_grade(student_id)
            requests.post(f"http://{flask_server.HOST}:{flask_server.PORT}/", json=grade)

        print("Work done!")
        QApplication.quit()

    @staticmethod
    def _generate_real_time_random_grade(student_id: int) -> Dict:
        # Notice that the order of key can be different with the header labels
        # of monitor, since monitor will re-order them properly.
        grade_point: float = randint(60, 100) / 100
        new_grade = {
            "id": student_id,
            "time": str(datetime.now()),
            "grade": grade_point,
            "status": "red" if grade_point < 0.8 else "green",
        }

        return new_grade


if __name__ == "__main__":
    app = QApplication(sys.argv)

    worker = ModelWoker()
    worker.work()

    sys.exit(app.exec())
