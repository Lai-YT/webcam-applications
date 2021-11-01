from PyQt5.QtGui import QResizeEvent
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from intergrated_gui.frame_widget import FrameWidget
from intergrated_gui.information_widget import InformationWidget
from intergrated_gui.panel_widget import PanelWidget


class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self._general_layout = QHBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)

        self._create_widgets()
        self._connect_signals()

        self._screen_size = QApplication.instance().primaryScreen().availableSize()
        # Limit the size to stay in comfort
        self.setMinimumSize(self._screen_size / 2)

    # Override
    def closeEvent(self, event):
        # Call the original implementation, which accepts and destroys the GUI
        # in default.
        super().closeEvent(event)
        # All other windows (no matter child or not) close with this window.
        QApplication.closeAllWindows()

    # Override
    def resizeEvent(self, event: QResizeEvent) -> None:
        # The frame widget is shown only when the window is big enough;
        # otherwise hide it to keep the window clean.
        # (also prevents the frame from distortion under unbalanced window size)
        new_size = event.size()
        if (new_size.width() < self._screen_size.width() * 0.8
                or new_size.height() < self._screen_size.height() * 0.8):
            self.widgets["frame"].hide()
            self.widgets["panel"].hide_frame_checkbox.setEnabled(False)
        else:
            self.widgets["frame"].show()
            self.widgets["panel"].hide_frame_checkbox.setEnabled(True)
        # still the resize is allowed
        super().resizeEvent(event)

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

    def _connect_signals(self):
        """Connect signal of hide_frame_checkbox."""
        self.widgets["panel"].hide_frame_checkbox.toggled.connect(
            lambda checked: self._hide_frame_widget(checked)
        )

    def _hide_frame_widget(self, checked: bool) -> None:
        if checked:
            self.widgets["frame"].hide()
        else:
            self.widgets["frame"].show()
