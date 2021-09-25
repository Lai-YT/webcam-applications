import sys

from PyQt5.QtWidgets import QApplication

from lib.brightness_window import BrightnessGui
from lib.brightness_controller import BrightnessController


app = QApplication(sys.argv)
# Create the plain GUI.
app_gui = BrightnessGui()
app_gui.show()
# Take control of the GUI and the Application.
controller = BrightnessController(app_gui)
# Execute the event loop.
sys.exit(app.exec_())