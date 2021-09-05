from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget

import gui.img.icon
from gui.page_widget import PageWidget


#     Current GUI layout:
#    -----------------------
#    | ------------------- | <- Central Widegt is a pure QWidget.
#    | |                 | <- General Layout margin of the Main GUI.
#    | |                 | |
#    | |      Pages  <- Created by PageWidget (OptionWidget, SettingWidget).
#    | |                 | |
#    | |                 | |
#    | ------------------- |
#    -----------------------

class ApplicationGui(QMainWindow):
    """This is the pure GUI part, provides no functionalitiy.
    It's responsibility is to create all components the GUI should have,
    whichs means no other components will be added by other parts (Controller, App).
    Functionality of the components is set by the Controllers.
    """

    def __init__(self):
        super().__init__()
        # Set some main window's properties.
        self.setWindowTitle("Webcam application")
        self.setWindowIcon(QIcon(":webcam.ico"))
        self.setFixedSize(400, 350)
        # Set the central widget and the general layout.
        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget(parent=self)
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Top is the page area.
        self._create_pages()

    def _create_pages(self):
        """Creates the page area. Components are created by PageWidget."""
        self.page_widget = PageWidget()
        self._general_layout.addWidget(self.page_widget)
