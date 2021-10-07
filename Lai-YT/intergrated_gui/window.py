from PyQt5.QtWidgets import QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from intergrated_gui.frame_widget import FrameWidget
from intergrated_gui.panel_widget import PanelWidget
from intergrated_gui.information_widget import InformationWidget


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self._general_layout = QHBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)

        self.create_widgets()

    def create_widgets(self):
        """
        Information widget at the left-hand side, capture view in the middle,
        control panel at the right.
        """
        # The number is the stretch of the widget.
        widgets = {
            "information": (InformationWidget(), 1),
            "frame": (FrameWidget(), 2),
            "panel": (PanelWidget(), 1),
        }
        self.widgets = {}
        for name, (widget, stretch) in widgets.items():
            self.widgets[name] = widget
            self._general_layout.addWidget(widget, stretch=stretch)
