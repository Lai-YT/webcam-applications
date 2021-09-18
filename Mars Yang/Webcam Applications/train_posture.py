import sys

from PyQt5.QtWidgets import QApplication

from gui.page_controller import ModelController
from gui.page_widget import ModelWidget


app = QApplication(sys.argv)
window = ModelWidget()
window.setFixedSize(500, 450)
window.show()
controller = ModelController(window)
sys.exit(app.exec_())