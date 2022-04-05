import requests


r = requests.get("http://127.0.0.1:5000/test")
print(r.status_code)
print(r.headers)
print(r.json())
