import time
import random
from datetime import datetime
from threading import Thread

import requests


# value of "time" will be added later
DATA = [
    {"id": 1, "time": "", "grade": 0.72},
    {"id": 2, "time": "", "grade": 0.77},
    {"id": 3, "time": "", "grade": 0.75},
    {"id": 1, "time": "", "grade": 0.67},
    {"id": 2, "time": "", "grade": 0.70},
    {"id": 3, "time": "", "grade": 0.68},
]


def post_grade(data):
    for datum in data:
        datum["time"] = datetime.now().strftime("%H:%M:%S")
        requests.post("http://127.0.0.1:5000/test", json=datum)
        time.sleep(random.random() * 2 + 1)


def main():
    threads = []
    for i in range(2):
        thread = Thread(target=post_grade, args=(DATA,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
