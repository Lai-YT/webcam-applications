import json

from flask import Flask, request


HOST = "127.0.0.1"
PORT = 5000

# Create flask instance.
app = Flask(__name__)

grade = []


@app.route("/grade", methods=["POST", "GET"])
def update_grade():
    if request.method == "POST":
        grade.append(request.get_json())
    elif request.method == "GET":
        # You still have to return the grade so can be "GET",
        # otherwise can always only get an empty list.
        ret_pack = grade.copy()
        grade.clear()
        return json.dumps(ret_pack)
    return json.dumps(grade)


screenshots = []


@app.route("/screenshot", methods=["POST", "GET"])
def update_screenshot():
    if request.method == "POST":
        screenshots.append(request.get_json())
    elif request.method == "GET":
        ret_pack = screenshots.copy()
        screenshots.clear()
        return json.dumps(ret_pack)
    return json.dumps(screenshots)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, threaded=True, use_reloader=False)
