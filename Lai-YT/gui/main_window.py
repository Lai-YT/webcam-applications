from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QGridLayout, QMainWindow, QVBoxLayout, QWidget

from gui.component import ActionButton
from gui.page_widget import PageWidget


#     Current GUI layout:
# 
#     -------------------
#     |      Pages      |  <- Created by PageWidget (OptionWidget, SettingWidget)
#     |                 |
#     -------------------
#     |  Action Buttons |  <- Created by main GUI
#     -------------------


# View is the pure GUI part, provides no functionalitiy.
# It's responsibility is to create all components the GUI should have,
# whichs means no other components will be added by other parts (Controller, Model).
# Functionality of the components is set by the Controllers.
class ApplicationGui(QMainWindow):
    """The main window that shows options of the application."""
    def __init__(self):
        super().__init__()
        # Set some main window's properties.
        self.setWindowTitle("Webcam application")
        self.setWindowIcon(QIcon("img/webcam.ico"))
        self.setFixedSize(400, 350)
        # Set the central widget and the general layout.
        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget(parent=self)
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Top is the page area.
        self._create_pages()
        # Action buttons at the bottom.
        self._create_buttons()

    def _create_pages(self):
        """Creates the page area. Components are created by PageWidget."""
        self.page_widget = PageWidget()
        self._general_layout.addWidget(self.page_widget)

    def _create_buttons(self):
        """Creates the common action buttons among pages."""
        self.action_buttons = {}
        buttons_layout = QGridLayout()
        # Button text | position on the QGridLayout
        buttons = {"Start": (0, 0), "Stop": (0, 1), "Exit": (0, 2)}
        # Create the buttons and add them to the grid layout.
        for btn_text, pos in buttons.items():
            self.action_buttons[btn_text] = ActionButton(btn_text)
            buttons_layout.addWidget(self.action_buttons[btn_text], *pos)

        self._general_layout.addLayout(buttons_layout)
