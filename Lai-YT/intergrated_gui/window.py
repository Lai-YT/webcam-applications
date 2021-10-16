from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from intergrated_gui.frame_widget import FrameWidget
from intergrated_gui.information_widget import InformationWidget
from intergrated_gui.panel_widget import PanelWidget
from intergrated_gui.panel_controller import PanelController


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self._general_layout = QHBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)

        self._create_widgets()

    # Override
    def closeEvent(self, event):
        # Call the original implementation, which accepts and destroys the GUI
        # in default.
        super().closeEvent(event)
        # All other windows (no matter child or not) close with this window.
        QApplication.closeAllWindows()

    def _create_widgets(self):
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
