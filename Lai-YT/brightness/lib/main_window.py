from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QGridLayout, QMainWindow, QVBoxLayout, QWidget
from lib.brightness_widget import BrightnessWidget

from lib.component import Button, Label, OptionRadioButton


class MainGui(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Brightness Optimization")
        self.resize(450, 300)
        self.setWindowIcon(QIcon("sun.ico"))

        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Initialize widgets
        self._set_label()
        self._set_ratio_buttons()
        self._set_buttons()

    # Override
    def closeEvent(self, event):
        # The sub-widgets such as BrightnessWidget is closed first when the user
        # closes the main window.
        QApplication.closeAllWindows()
        # Call the original implementation, which accepts and destroys the GUI
        # in default.
        super().closeEvent(event)

    def _set_label(self):
        self.label = Label("Please choose the optimization mode\n you prefer.", font_size=15)
        self._general_layout.addWidget(self.label)

    def _set_ratio_buttons(self):
        self.modes = {}
        modes_layout = QVBoxLayout()
        modes_layout.setAlignment(Qt.AlignVCenter)
        # Mode name | description
        modes = {
            "webcam": "Webcam-based brightness detector \n(webcam required)",
            "color-system": "Color-system mode",
        }
        for mode, des in modes.items():
            self.modes[mode] = OptionRadioButton(des, font_size=12)
            modes_layout.addWidget(self.modes[mode])

        self._general_layout.addLayout(modes_layout)

    def _set_buttons(self):
        self.buttons = {}
        buttons_layout = QGridLayout()
        # Button text | position on the QGridLayout
        buttons = {"Start": (0, 0), "Exit": (0, 1)}
        # Create the buttons and add them to the grid layout.
        for name, pos in buttons.items():
            self.buttons[name] = Button(name)
            buttons_layout.addWidget(self.buttons[name], *pos)

        self._general_layout.addLayout(buttons_layout)
