from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from lib.component import Button, Label

class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Screen color detector")

        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Initialize widgets
        self._set_buttons()

    def _set_buttons(self):
        self.button = Button("screenshot")
        self._general_layout.addWidget(self.button)
