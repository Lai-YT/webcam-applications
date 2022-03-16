from binhex import openrsrc
import json
import requests
import time


def main():
    f = open("grade.json")
    data = json.load(f)

    counter = 0
    while True:
        # post the value of the counter every second
        requests.post("http://127.0.0.1:5000/test", json=data)
        counter += 1
        time.sleep(1)

if __name__ == "__main__":
    main()
