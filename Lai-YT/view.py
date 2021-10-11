import sys

from PyQt5.QtWidgets import QApplication

from intergrated_gui.window_controller import WindowController
from intergrated_gui.window import Window


app = QApplication([])
window = Window()
controller = WindowController(window)
window.showMaximized()
sys.exit(app.exec_())
