from typing import Dict, List

from flask import Flask, jsonify, render_template, request


HOST = "127.0.0.1"
PORT = 5000

# Create flask instance.
app = Flask(__name__)


@app.route("/")
def home():
    return render_template("index.html")


data: Dict[str, List] = {
    "grades": [],
    "screenshots": [],
}


@app.route("/teacher", methods=["GET"])
def get_data():
    # get certain data by passing `genre` as parameter
    if "genre" in request.args and request.args["genre"] in data.keys():
        # the data are cleared after being gotten
        res_data = data[request.args["genre"]].copy()
        data[request.args["genre"]].clear()
        return jsonify(res_data)
    return render_template("data.html", **data)


@app.route("/student/grades", methods=["POST"])
def update_grade():
    new_grade = request.get_json()
    data["grades"].append(new_grade)
    return jsonify(new_grade)


@app.route("/student/screenshots", methods=["POST"])
def update_screenshot():
    new_screenshot = request.get_json()
    data["screenshots"].append(new_screenshot)
    return jsonify(new_screenshot)


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, threaded=True, use_reloader=False)
