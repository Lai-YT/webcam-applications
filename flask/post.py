from binhex import openrsrc
import json
import requests
import time


def main():
    f = open("grade.json")
    data = json.load(f)

    while True:
        # Post grades one by one every two seconds.
        for grade in data["grades"]:
            requests.post("http://127.0.0.1:5000/test", json=grade)
            time.sleep(2)

if __name__ == "__main__":
    main()
