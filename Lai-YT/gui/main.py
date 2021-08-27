import sys

from PyQt5.QtWidgets import QApplication

from controller import GuiController
from view import ApplicationGui


if __name__ == '__main__':
    app = QApplication(sys.argv)
    # Create the plain GUI.
    app_gui = ApplicationGui()
    app_gui.show()
    # Take control of the GUI.
    GuiController(gui=app_gui)
    # Execute the event loop.
    sys.exit(app.exec_())
