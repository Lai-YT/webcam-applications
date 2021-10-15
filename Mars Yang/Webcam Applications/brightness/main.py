import sys

from PyQt5.QtWidgets import QApplication

from lib.main_controller import GuiController
from lib.main_window import MainGui


app = QApplication(sys.argv)
# Create the plain GUI.
app_gui = MainGui()
app_gui.show()
# Take control of the GUI and the Application.
controller = GuiController(app_gui)
# Execute the event loop.
sys.exit(app.exec_())
