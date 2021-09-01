from PyQt5.QtWidgets import QFormLayout, QGridLayout, QTabWidget, QWidget

from gui.component import Label, LineEdit, OptionCheckBox, MessageLabel


class PageWidget(QTabWidget):
    """PageWidget contains the widgets that are switchable."""
    def __init__(self):
        super().__init__()
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
    def __init__(self):
        super().__init__()
        self._create_options()

    def _create_options(self):
        """Create the options of this widget."""
        # Each check box followed by a label, which shows message when error occurs.
        self.options = {}
        self.messages = {}
        # Option name | order
        options_layout = QGridLayout()
        options = {
            "Distance Measure": 0,
            "Focus Time": 1,
            "Posture Detect": 2,
        }
        for opt, row in options.items():
            self.options[opt] = OptionCheckBox(opt)
            options_layout.addWidget(self.options[opt], row, 0)
            # A message label is 2 columns long.
            self.messages[opt] = MessageLabel()
            options_layout.addWidget(self.messages[opt], row, 1, 1, 2)

        self.setLayout(options_layout)


class SettingWidget(QWidget):
    """The input area of  settings/parameters that the application needs are put here."""
    def __init__(self):
        super().__init__()
        self._create_settings()

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

        self.setLayout(settings_layout)
