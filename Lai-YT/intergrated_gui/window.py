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

    # Override
    def resizeEvent(self, event):
        # Prevent the information widget from expanding by the inner labels.
        total_stretch = self._get_total_stretch()
        information_stretch = self._general_layout.stretch(self._general_layout.indexOf(self.widgets["information"]))
        self.widgets["information"].setFixedSize(
            self.frameGeometry().width() * information_stretch // total_stretch,
            self.widgets["information"].sizeHint().height()
        )

        super().resizeEvent(event)

    def _get_total_stretch(self):
        total = 0
        for i in range(len(self.widgets)):
            total += self._general_layout.stretch(i)
        return total

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
