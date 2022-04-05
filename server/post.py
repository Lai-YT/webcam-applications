import json
import time

import requests


def post_grade(data):
    for grade in data["grades"]:
        requests.post("http://127.0.0.1:5000/test", json=grade)
        time.sleep(1)


def main():
    with open("grade.json") as f:
        data = json.load(f)
    # posting is outside of "with" to have the file closed as early
    # as possible
    post_grade(data)


if __name__ == "__main__":
    main()
