from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout
from PyQt5.QtWidgets import QGridLayout
from PyQt5.QtWidgets import QMainWindow
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

from component import ActionButton, OptionCheckBox, Label, LineEdit


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
        self._init_options()
        self._init_settings()
        self._init_buttons()

    def _init_options(self):
        self._general_layout.addWidget(Label("Options:"))
        # Each check box followed by a label, which shows message when error occurs.
        self.options = {}
        self.option_msgs = {}
        options_layout = QGridLayout()
        options = {"Distance Measure": 0,
                   "Timer": 1,
                   "Posture Detection": 2,}
        for opt, row in options.items():
            self.options[opt] = OptionCheckBox(opt)
            options_layout.addWidget(self.options[opt], row, 0)
            # A message label is 2 columns long.
            options_layout.addWidget(Label(), row, 1, 1, 2)

        self._general_layout.addLayout(options_layout)

    def _init_settings(self):
        self._general_layout.addWidget(Label("Settings:"))
        self.settings = {}
        settings_layout = QFormLayout()
        # Parameter's name | description
        settings = {"Face Width": "Face width:",
                    "Distance": "Distance from screen:",}
        for set, text in settings.items():
            self.settings[set] = LineEdit("0~99.99 (cm)")
            settings_layout.addRow(Label(text), self.settings[set])

        self._general_layout.addLayout(settings_layout)

    def _init_buttons(self):
        self.action_buttons = {}
        buttons_layout = QGridLayout()
        # Button text | position on the QGridLayout
        buttons = {"Start": (0, 0), "Restart": (0, 1), "Exit": (0, 2),}
        # Create the buttons and add them to the grid layout.
        for btn_text, pos in buttons.items():
            self.action_buttons[btn_text] = ActionButton(btn_text)
            buttons_layout.addWidget(self.action_buttons[btn_text], *pos)

        self._general_layout.addLayout(buttons_layout)
