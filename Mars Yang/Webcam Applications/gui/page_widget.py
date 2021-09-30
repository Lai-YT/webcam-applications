from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (QFormLayout, QGridLayout, QGroupBox, QHBoxLayout,
                             QTabWidget, QVBoxLayout, QWidget)

from gui.component import (ActionButton, Label, LineEdit, OptionCheckBox,
                           OptionRadioButton, MessageLabel)


class PageWidget(QTabWidget):
    """PageWidget contains the widgets that are switchable."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Set font of the page switching buttons.
        self.tabBar().setStyleSheet('font: 12pt "Arial";')
        self._create_pages()

    def _create_pages(self):
        """Create the pages of this widget."""
        self.pages = {
            "Options": OptionWidget(),
            "Settings": SettingWidget(),
            "Model": ModelWidget(),
        }
        for text, page in self.pages.items():
            self.addTab(page, text)


class OptionWidget(QWidget):
    """The options of the application are put here."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # A wiget can only have 1 layout.
        # A simple walk around is to create a main layout and add sub layout/widget into it.
        self._general_layout = QVBoxLayout()
        self.setLayout(self._general_layout)

        self._create_options()
        self._create_buttons()

    def _create_options(self):
        """Create the options of this widget."""
        # Each check box followed by a label, which shows message when error occurs.
        self.options = {}
        options_layout = QVBoxLayout()
        # Option name | description
        options = {
            "Distance Measure": "shows message if the user gets too close to the screen",
            "Focus Time": "reminds when it's time to take a break",
            "Posture Detect": "shows message when the user has bad posture",
        }
        for opt, des in options.items():
            self.options[opt] = OptionCheckBox(opt)
            options_layout.addWidget(self.options[opt], stretch=1)
            options_layout.addWidget(Label("    " + des, font_size=10), stretch=1)
        self._general_layout.addLayout(options_layout)

        self._create_model_options()
        
        self.message = MessageLabel()
        self._general_layout.addWidget(self.message)

    def _create_model_options(self):
        # Add exclusive option buttons.
        group_box = QGroupBox(title="Please choose the model to use.")
        group_box.setFont(QFont("Arial", 10))
        options_layout = QVBoxLayout()
        group_box.setLayout(options_layout)
        self._general_layout.addWidget(group_box)

        # name : OptionRadioButton
        self.model_options = {}
        model_options = ["Default", "Custom"]
        for name in model_options:
            self.model_options[name] = OptionRadioButton(name, font_size=10)
            options_layout.addWidget(self.model_options[name])

    def _create_buttons(self):
        """Creates the buttons of actions"""
        self.buttons = {}
        buttons_layout = QGridLayout()
        # Button text | position on the QGridLayout
        buttons = {"Start": (0, 0), "Stop": (0, 1), "Exit": (0, 2)}
        # Create the buttons and add them to the grid layout.
        for btn_text, pos in buttons.items():
            self.buttons[btn_text] = ActionButton(btn_text)
            buttons_layout.addWidget(self.buttons[btn_text], *pos)

        self._general_layout.addLayout(buttons_layout)


class SettingWidget(QWidget):
    """The input area of settings/parameters that the application needs are put here."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._general_layout = QVBoxLayout()
        self.setLayout(self._general_layout)

        self._create_settings()
        self._create_buttons()

    def _create_settings(self):
        """Create the settings of this widget."""
        self.settings = {}
        settings_layout = QFormLayout()
        # {option: [(parameter, description)]}
        settings = {
            "Distance Measure": [
                ("Face Width","Face width:"),
                ("Distance","Distance in reference:"),
                ("Bound","Shortest distance allowed:"),
            ],
            "Focus Time": [
                ("Time Limit", "Time limit:"),
                ("Break Time", "Break time:"),
            ],
            "Posture Detect": [
                ("Angle", "Allowed slope angle:"),
            ],
        }
        for option, parameters in settings.items():
            settings_layout.addRow(Label("<b>" + option + "</b>"))
            self.settings[option] = {}
            for param, descript in parameters:
                self.settings[option][param] = LineEdit()
                settings_layout.addRow(Label(descript), self.settings[option][param])

        # The message label occupies a whole row.
        self.message = MessageLabel()
        settings_layout.addRow(self.message)

        self._general_layout.addLayout(settings_layout)

    def _create_buttons(self):
        """Creates buttons of the widget."""
        self.buttons = {"Save": ActionButton("Save")}
        self._general_layout.addWidget(self.buttons["Save"], alignment=Qt.AlignRight | Qt.AlignBottom)


class ModelWidget(QWidget):
    """This is the widget that provides interface of model training options."""
    def __init__(self, parent=None):
        super().__init__(parent)

        self._general_layout = QVBoxLayout()
        self.setLayout(self._general_layout)

        self._create_options()
        self._create_buttons()

    def _create_options(self):
        # Add a QGroupBox to the general layout.
        # The OptionRadioButton contained are exclusive.
        group_box = QGroupBox(title="Here you can customize your own posture model.")
        group_box.setFont(QFont("Arial", 12))
        options_layout = QVBoxLayout()
        group_box.setLayout(options_layout)
        self._general_layout.addWidget(group_box)

        # Add buttons into the QGroupBox.
        # Option name | description
        options = {
            "Good": "capture sample images of good, healthy posture when writing in front of the screen",
            "Slump": "capture sample images of poor, slumped posture when writing in front of the screen"
        }
        # option name : button
        self.options = {}
        for name, des in options.items():
            self.options[name] = OptionRadioButton(name)
            options_layout.addWidget(self.options[name])
            # Wrap word due to long description.
            options_layout.addWidget(Label(des, font_size=10, wrap=True))

    def _create_buttons(self):
        """Creates buttons of the widget."""
        self.buttons = {}
        buttons = ["Train", "Finish", "Capture"]
        buttons_layout = QHBoxLayout()
        # Keep a space in the left.
        buttons_layout.addStretch(1)
        for name in buttons:
            self.buttons[name] = ActionButton(name)
            buttons_layout.addWidget(self.buttons[name], alignment=Qt.AlignBottom, stretch=1)

        self._general_layout.addLayout(buttons_layout)
