import json

from flask import Flask, request


# Create flask instance.
app = Flask(__name__)

data = []
@app.route("/test", methods=["POST", "GET"])
def update_grade():
    if request.method == "POST":
        data.append(request.get_json())
    return json.dumps(data)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, threaded=True, use_reloader=False, debug=True)
