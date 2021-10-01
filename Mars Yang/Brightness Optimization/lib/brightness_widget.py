from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QMessageBox, QVBoxLayout, QWidget

from lib.component import Button, CheckBox, HorizontalSlider, Label


class BrightnessWidget(QWidget):

    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Auto Brightness Controller")
        self.resize(450, 300)
        self.setWindowIcon(QIcon("sun.ico"))

        self._general_layout = QVBoxLayout()
        # Initialize widgets
        self._set_label()
        self._set_slider()
        self._set_checkbox()
        self._set_buttons()
    
    # Override
    def closeEvent(self, event):
        """A clean up function is called before closed if set."""
        # If there exists clean up callback, call it before passing the event
        # to the original implementation.
        if callable(getattr(self, "_clean_up_callback", False)):
            self._clean_up_callback()
        # Call the original implementation, which accepts and destroys the GUI
        # in default.
        super().closeEvent(event)

    def set_clean_up_before_destroy(self, clean_up_callback):
        """Sets the clean up function to give the ability to do extra process
        before the GUI destroyed.

        Arguments:
            clean_up_callback (Callable[[], Any]): Is called before the GUI destroyed
        """
        self._clean_up_callback = clean_up_callback

    def _set_label(self):
        self.label = Label()
        self._general_layout.addWidget(self.label)

    def _set_slider(self):
        self.slider = HorizontalSlider()
        self._general_layout.addWidget(self.slider)

    def _set_checkbox(self):
        self.checkbox = CheckBox("Brightness Optimization")

        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.checkbox)
        checkbox_layout.setAlignment(Qt.AlignHCenter)
        self._general_layout.addLayout(checkbox_layout)

    def _set_buttons(self):
        self.buttons = {}
        buttons = {"Exit": "Exit"}

        for name, text in buttons.items():
            self.buttons[name] = Button(text)
            self._general_layout.addWidget(self.buttons[name])

class WarningWidget(QDialog):
    def __init__(self):
        super().__init__() 

        self.setWindowTitle("Warning")
        self.setWindowIcon(QIcon("warning.ico"))
        self.setFixedSize(545, 160)

        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget(parent=self)
        self._central_widget.setLayout(self._general_layout)

        self._set_warning_text()
        self._set_checkbox()
        self._set_button()

    def _set_warning_text(self):
        self._warning_text = Label(font_size=15, wrap=False)
        self._warning_text.setText("High brightness may reduce CPU performance\n and harm you sight.")
        self._warning_text.setAlignment(Qt.AlignCenter)
        self._general_layout.addWidget(self._warning_text)

    def _set_checkbox(self):
        self.checkbox = CheckBox("Don't remind me again.")

        checkbox_layout = QVBoxLayout()
        checkbox_layout.addWidget(self.checkbox)
        checkbox_layout.setAlignment(Qt.AlignHCenter)
        self._general_layout.addLayout(checkbox_layout)

    def _set_button(self):
        self.button = Button(text="OK")
        self._general_layout.addWidget(self.button)


