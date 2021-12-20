import sys

from PyQt5.QtWidgets import QApplication

from app.webcam_application import WebcamApplication
from gui.main_controller import GuiController
from gui.main_window import ApplicationGui


app = QApplication(sys.argv)
# Create the plain GUI.
app_gui = ApplicationGui()
# Create the application.
webcam_app = WebcamApplication()
# Take control of the GUI and the Application.
controller = GuiController(app_gui, webcam_app)
# Execute the event loop.
app_gui.show()
sys.exit(app.exec())
