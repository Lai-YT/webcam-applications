from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFormLayout, QGridLayout, QSpacerItem, QTabWidget, QVBoxLayout, QWidget

from gui.component import ActionButton, Label, LineEdit, OptionCheckBox, MessageLabel


class PageWidget(QTabWidget):
    """PageWidget contains the widgets that are switchable."""
    def __init__(self, parent=None):
        super().__init__(parent)
        # Set font of the page switching buttons.
        self.tabBar().setStyleSheet('font: 12pt "Arial";')
        self._create_pages()

    def _create_pages(self):
        """Create the pages of this widget."""
        self.pages = {"Options": OptionWidget(), "Settings": SettingWidget()}
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
        # Option name | order
        options_layout = QVBoxLayout()
        options = ["Distance Measure", "Focus Time", "Posture Detect"]
        for opt in options:
            self.options[opt] = OptionCheckBox(opt)
            options_layout.addWidget(self.options[opt], stretch=1)
        # Add space to make options close together.
        options_layout.addStretch(5)

        self.message = MessageLabel()
        options_layout.addWidget(self.message)

        self._general_layout.addLayout(options_layout)

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
        # Parameter name | description
        settings = {
            "Face Width": "Face width:",
            "Distance": "Distance from screen:",
        }
        for set, text in settings.items():
            self.settings[set] = LineEdit()
            settings_layout.addRow(Label(text), self.settings[set])

        self.message = MessageLabel()
        # The message label occupies a whole row.
        settings_layout.addRow(self.message)
    
        self._general_layout.addLayout(settings_layout)

    def _create_buttons(self):
        self.save_button = ActionButton("Save")
        self._general_layout.addWidget(self.save_button, alignment=Qt.AlignRight | Qt.AlignBottom)
        