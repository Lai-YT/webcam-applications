import json

from flask import Flask, request


HOST = "127.0.0.1"
PORT = 5000

# Create flask instance.
app = Flask(__name__)

data = []
@app.route("/", methods=["POST", "GET"])
def update_grade():
    if request.method == "POST":
        data.append(request.get_json())
    elif request.method == "GET":
        # You still have to return the data so can be "GET",
        # otherwise can always only get an empty list.
        ret_pack = data.copy()
        data.clear()
        return json.dumps(ret_pack)
    return json.dumps(data)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, threaded=True, use_reloader=False)
