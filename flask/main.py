import json
import sys

from flask import Flask, request
from threading import Thread
from PyQt5.QtWidgets import QApplication

from gui.conrtoller import GuiController
from gui.window import FlaskGui


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Create the plain GUI.
    window = FlaskGui()
    window.show()
    controller = GuiController(window, app)
    # Create flask instance.
    app_ = Flask(__name__)

    data = []
    @app_.route("/test", methods=["POST", "GET"])
    def create_data():
        if request.method == "POST":
            res = request.get_json() # a list with a value of the counter

            # Extend the initial list instead of appending
            # a new list.
            data.extend(res)
            controller.update_counter(data)
        # Convert the list to json string.
        return json.dumps(data)

    kwargs = {
        "host": "127.0.0.1",
        "port": 5000,
        "threaded": True,
        "use_reloader": False,
        "debug": True
    }
    flaskThread = Thread(target=app_.run, daemon=True, kwargs=kwargs).start()
    app.exec_()
