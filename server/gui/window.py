from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from gui.component import Label, LineEdit, PullDownMenu


class FlaskGui(QMainWindow):
    def __init__(self):
        super().__init__()
        # Set some main window's properties.
        self.setWindowTitle("flask test")
        self.setFixedSize(560, 420)
        # Set the central widget and the general layout.
        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)

        self._create_label()
        self._create_pull_down_menu()
        self._create_input_line()
    
    def _create_label(self):
        self.label = Label("No grade received.", wrap=True)
        self._general_layout.addWidget(self.label, alignment=Qt.AlignCenter)

    def _create_pull_down_menu(self):
        self.menu = PullDownMenu()
        self.menu.add_item("A01")
        self.menu.add_item("A02")
        self.menu.add_item("A03")
        self._general_layout.addWidget(self.menu, alignment=Qt.AlignCenter)

    def _create_input_line(self):
        self.input_line = LineEdit("Enter new ID to create table.")
        self._general_layout.addWidget(self.input_line, alignment=Qt.AlignCenter)
