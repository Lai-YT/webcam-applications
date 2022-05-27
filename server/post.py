import time
import random
from datetime import datetime
from threading import Thread

import requests

import server.main as flask_server


# value of "time" and "grade" will be set later
DATA = [
    [
        {"id": "1", "time": "", "grade": -1},
        {"id": "2", "time": "", "grade": -1},
        {"id": "3", "time": "", "grade": -1},
        {"id": "4", "time": "", "grade": -1},
        {"id": "5", "time": "", "grade": -1},
        {"id": "6", "time": "", "grade": -1},
    ],
    [
        {"id": "7", "time": "", "grade": -1},
        {"id": "8", "time": "", "grade": -1},
        {"id": "9", "time": "", "grade": -1},
        {"id": "10", "time": "", "grade": -1},
        {"id": "11", "time": "", "grade": -1},
        {"id": "12", "time": "", "grade": -1},
    ],
    [
        {"id": "10", "time": "", "grade": -1},
        {"id": "11", "time": "", "grade": -1},
        {"id": "12", "time": "", "grade": -1},
        {"id": "13", "time": "", "grade": -1},
        {"id": "14", "time": "", "grade": -1},
        {"id": "15", "time": "", "grade": -1},
        {"id": "16", "time": "", "grade": -1},
        {"id": "17", "time": "", "grade": -1},
        {"id": "18", "time": "", "grade": -1},
    ],
    [
        {"id": "19", "time": "", "grade": -1},
        {"id": "20", "time": "", "grade": -1},
        {"id": "21", "time": "", "grade": -1},
        {"id": "22", "time": "", "grade": -1},
        {"id": "23", "time": "", "grade": -1},
        {"id": "24", "time": "", "grade": -1},
    ],
]

DATE_STR_FORMAT = "%Y-%m-%d, %H:%M:%S"


def post_grade(data):
    for _ in range(3):  # each "id" will be sent 3 times
        for datum in data:
            datum["time"] = datetime.now().strftime(DATE_STR_FORMAT)
            datum["grade"] = random.randint(60, 100) / 100

            requests.post(
                f"http://{flask_server.HOST}:{flask_server.PORT}/grade", json=datum
            )
            # 1 ~ 2 sec delay between datum
            time.sleep(random.random() + 1)
        # 2 ~ 3 sec delay between data
        time.sleep(random.random() + 2)


def main():
    threads = []
    for i, data in enumerate(DATA):
        thread = Thread(target=post_grade, args=(data,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
