import sys

from PyQt5.QtWidgets import QApplication

from app.webcam_application_ import WebcamApplication
from intergrated_gui.window_controller import WindowController
from intergrated_gui.window import Window


app = QApplication([])
window = Window()
app_ = WebcamApplication()
controller = WindowController(window, app_)
window.show()
sys.exit(app.exec_())
