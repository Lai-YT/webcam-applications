import json
import time

import requests


def post_grade_every_second(data):
    for grade in data["grades"]:
        requests.post("http://127.0.0.1:5000/test", json=grade)
        time.sleep(1)


def main():
    with open("grade.json") as f:
        data = json.load(f)
        post_grade_every_second(data)


if __name__ == "__main__":
    main()
