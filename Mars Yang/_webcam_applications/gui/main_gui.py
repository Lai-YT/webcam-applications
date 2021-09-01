from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QGridLayout, QMainWindow, QVBoxLayout, QWidget

from gui.component import ActionButton, OptionCheckBox, Label


# View is the pure GUI part, provides no functionalitiy.
# It's responsibility is to create all components the GUI should have,
# whichs means no other components will be added by other parts (Controller, Model).
# Functionality of the components is set by the Controller.
class ApplicationGui(QMainWindow):
    """The main window that shows options of the application."""
    def __init__(self):
        super().__init__()
        # Set some main window's properties.
        self.setWindowTitle("Webcam application")
        self.setWindowIcon(QIcon("img/webcam.ico"))
        self.setFixedSize(400, 300)
        # Set the central widget and the general layout.
        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget(parent=self)
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Create check boxes for options, line edits for settings of parameter
        # and buttons to start and exit.
        self._create_options()
        self._create_buttons()

    def _create_options(self):
        # Each check box followed by a label, which shows message when error occurs.
        self.options = {}
        # Option name | order
        options_layout = QGridLayout()
        options = {
            "Distance Measure": 0,
            "Focus Time": 1,
            "Posture Detect": 2,
        }
        
        options_layout.addWidget(Label("Options:"), 0, 0) # title label
        for opt, row in options.items():
            self.options[opt] = OptionCheckBox(opt)
            options_layout.addWidget(self.options[opt], row+1, 0)

        self._general_layout.addLayout(options_layout)

    def _create_buttons(self):
        self.action_buttons = {}
        buttons_layout = QGridLayout()
        # Button text | position on the QGridLayout
        buttons = {"Start": (0, 0), "Stop": (0, 1), "Exit": (0, 2), "Settings": (1, 1)}
        # Create the buttons and add them to the grid layout.
        for btn_text, pos in buttons.items():
            self.action_buttons[btn_text] = ActionButton(btn_text)
            buttons_layout.addWidget(self.action_buttons[btn_text], *pos)

        self._general_layout.addLayout(buttons_layout)
