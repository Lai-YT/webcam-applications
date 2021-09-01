from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QFormLayout, QGridLayout, QMainWindow, QVBoxLayout, QWidget

from gui.component import ActionButton, MessageLabel, Label, LineEdit


# View is the pure GUI part, provides no functionalitiy.
# It's responsibility is to create all components the GUI should have,
# whichs means no other components will be added by other parts (Controller, Model).
# Functionality of the components is set by the Controller.
class SettingsGui(QMainWindow):
    """The main window that shows options of the application."""
    def __init__(self):
        super().__init__()
        # Set some main window's properties.
        self.setWindowTitle("Settings")
        self.setWindowIcon(QIcon("img/webcam.ico"))
        self.setFixedSize(400, 300)
        # Set the central widget and the general layout.
        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget(parent=self)
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Create check boxes for options, line edits for settings of parameter
        # and buttons to start and exit.
        self._create_settings()
        self._create_buttons()
        self._create_warning_box()


    def _create_settings(self):
        self._general_layout.addWidget(Label("Settings:"))
        self.settings = {}
        self.labels = {}
        settings_layout = QFormLayout()
        # Parameter name | description
        settings = {
            "Face Width": "Face width:",
            "Distance": "Distance from screen:",
        }
        for set, text in settings.items():
            self.settings[set] = LineEdit()
            settings_layout.addRow(Label(text), self.settings[set])
        self._general_layout.addLayout(settings_layout)


    def _create_buttons(self):
        self.action_buttons = {}
        buttons_layout = QGridLayout()
        # Button text | position on the QGridLayout
        buttons = {"Confirm": (0, 0)}
        # Create the buttons and add them to the grid layout.
        for btn_text, pos in buttons.items():
            self.action_buttons[btn_text] = ActionButton(btn_text)
            buttons_layout.addWidget(self.action_buttons[btn_text], *pos)

        self._general_layout.addLayout(buttons_layout)

    def _create_warning_box(self):
        warning_layout = QGridLayout()
        self.warning_label = MessageLabel()
        warning_layout.addWidget(self.warning_label, 0, 1)
        self._general_layout.addLayout(warning_layout)