import time
import random
from datetime import datetime, timedelta
from threading import Thread

import requests

import server.main as flask_server


STUDENT_IDS = [
    ["108AB0001", "108AB0002", "108AB0003", "108AB0004", "108AB0005", "108AB0006"],
    ["108AB0007", "108AB0008", "108AB0009", "108AB0010", "108AB0011", "108AB0012"],
    ["108AB0013", "108AB0014", "108AB0015", "108AB0016", "108AB0017", "108AB0018"],
    ["108AB0019", "108AB0020", "108AB0021", "108AB0022", "108AB0023", "108AB0024"],
]

DATE_STR_FORMAT = "%Y-%m-%d, %H:%M:%S"
REF_TIME = datetime(2022, 5, 5, 10, 10)

def post_grade(student_ids):
    for i in range(50):
        for student_id in student_ids:
            data = {
                "id": student_id,
                "time": (REF_TIME + timedelta(minutes=i+1)).strftime(DATE_STR_FORMAT),
                "grade": random.randint(60, 100) / 100,
            }

            requests.post(f"http://{flask_server.HOST}:{flask_server.PORT}/grade", json=data)
        #     # 1 ~ 2 sec delay between datum
        #     time.sleep(random.random() + 1)
        # # 2 ~ 3 sec delay between data
        # time.sleep(random.random() + 2)


def main():
    threads = []
    for i, student_ids in enumerate(STUDENT_IDS):
        thread = Thread(target=post_grade, args=(student_ids,))
        threads.append(thread)
        thread.start()
    for thread in threads:
        thread.join()


if __name__ == "__main__":
    main()
