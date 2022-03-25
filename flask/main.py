import json
import sys
from threading import Thread

from PyQt5.QtWidgets import QApplication
from flask import Flask, request

from gui.controller import GuiController
from gui.window import FlaskGui


# Create flask instance.
app_ = Flask(__name__)

@app_.route("/test", methods=["POST", "GET"])
def update_grade():
    if request.method == "POST":
        grade = request.get_json()
        controller.store_grade_in_database(grade)
    return ""


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Create the plain GUI and controller.
    window = FlaskGui()
    controller = GuiController(window, app)
    window.show()

    kwargs = {
        "host": "127.0.0.1",
        "port": 5000,
        "threaded": True,
        "use_reloader": False,
        "debug": True,
    }
    Thread(target=app_.run, kwargs=kwargs, daemon=True).start()
    sys.exit(app.exec_())
