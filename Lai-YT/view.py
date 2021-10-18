import sys

from PyQt5.QtWidgets import QApplication

from intergrated_gui.window_controller import WindowController
from intergrated_gui.window import Window
from lib.app_ import WebcamApplication


app = QApplication([])
window = Window()
app_ = WebcamApplication()
controller = WindowController(window, app_)
window.showMaximized()
sys.exit(app.exec_())
