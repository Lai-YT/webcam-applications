from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QFormLayout, QDialog

from gui.component import ActionButton, Label, LineEdit, OptionCheckBox, MessageLabel


# Current GUI layout: I don't know...

class BreakGui(QDialog):

    def __init__(self):
        super().__init__()
        # Set some main window's properties.
        self.setWindowTitle("Break Time!!")
        self.setWindowIcon(QIcon(":webcam.ico"))
        self.setFixedSize(700, 300)
        # Set the central widget and the general layout.
        self._general_layout = QVBoxLayout()
        # self._central_widget = QWidget(parent=self)
        # self._central_widget.setLayout(self._general_layout)
        # self.setCentralWidget(self._central_widget)
        
        self._break()

    def _break(self):
        break_layout = QFormLayout()
        break_text = "It's time to take a break!"
        self.break_message = Label(text=break_text, font_size=20)
        self.break_message.setAlignment(Qt.AlignCenter)
        self.countdown_message = MessageLabel(font_size=20)
        self.countdown_message.setAlignment(Qt.AlignCenter)
        break_layout.addRow(self.break_message)
        break_layout.addRow(self.countdown_message)

        self._general_layout.addLayout(break_layout)

            