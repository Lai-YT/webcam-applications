import sys

from PyQt5.QtWidgets import QApplication

from intergrated_gui.window import Window


app = QApplication([])
window = Window()
window.showMaximized()
sys.exit(app.exec_())
