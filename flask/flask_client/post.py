import requests
import time


def main():
    counter = 0
    while True:
        # post the value of the counter every second
        requests.post("http://127.0.0.1:5000/test", json=[counter])
        counter += 1
        time.sleep(1)

if __name__ == "__main__":
    main()
