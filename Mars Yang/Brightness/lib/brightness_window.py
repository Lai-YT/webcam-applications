from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


class BrightnessGui(QMainWindow):

    def __init__(self, parent=None):
        super(BrightnessGui, self).__init__(parent)

        self.setWindowTitle("Auto Brightness Controller")
        self.resize(450, 300)
        self.setWindowIcon(QIcon("sun.ico"))
        # Set layout
        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget(parent=self)
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        # Initialize widgets
        self.set_label()
        self.set_checkbox()
        self.set_slider()
        self.set_button()
        # Initialize exit flag.
        self.exit_flag = False

    def set_label(self):
        """Set a label on the window."""
        self.label = QLabel()
        self.label.setFont(QFont("Arial", 35))
        self.label.setAlignment(Qt.AlignCenter)
        self._general_layout.addWidget(self.label)

    def set_checkbox(self):
        """Set a checkbox on the window."""
        self.lock = QCheckBox("Lock Brightness")
        self.lock.setFont(QFont("Arial", 14))
        # Align center
        self.lock.setStyleSheet("margin-left:115%; margin-right:100%;")
        self.lock.hide()
        self._general_layout.addWidget(self.lock)

    def set_slider(self):
        """Set a horizontal slider on the window."""
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(60)
        self.slider.setSingleStep(3)
        self.slider.setValue(20)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(5)
        self._general_layout.addWidget(self.slider)

    def set_button(self):
        """Set a capture button on the window."""
        self.start = QPushButton()
        self.start.setText("Start Capturing")
        self.start.setFont(QFont("Arial", 12))
    
        self.exit = QPushButton()
        self.exit.setText("Exit")
        self.exit.setFont(QFont("Arial", 12))
        self.exit.setEnabled(False)

        self._general_layout.addWidget(self.start)
        self._general_layout.addWidget(self.exit)