import sys

from PyQt5.QtWidgets import QApplication

from lib.main_window import MainWindow
from lib.main_controller import MainController

app = QApplication(sys.argv)
# Create the plain GUI.
app_gui = MainWindow()
app_gui.show()
# Take control of the GUI and the Application.
controller = MainController(app_gui)
# Execute the event loop.
sys.exit(app.exec_())