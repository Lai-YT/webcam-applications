import sys

from PyQt5.QtWidgets import QApplication

from gui.main_window import ApplicationGui
from main_controller import GuiController


app = QApplication(sys.argv)
# Create the plain GUI.
app_gui = ApplicationGui()
app_gui.show()
# Take control of the GUI and the Application.
controller = GuiController(app_gui)
# Execute the event loop.
sys.exit(app.exec())
