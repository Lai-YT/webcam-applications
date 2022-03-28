import sys

from PyQt5.QtWidgets import QApplication

from app.webcam_application import WebcamApplication
from gui.window_controller import WindowController
from gui.window import Window


app = QApplication(sys.argv)
# Create the plain GUI.
window = Window()
# Take control of the GUI and the Application.
webcam_app = WebcamApplication()
controller = WindowController(window, webcam_app)
# Execute the event loop.
window.show()
sys.exit(app.exec_())
