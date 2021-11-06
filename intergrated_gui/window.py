from typing import Any, Callable, Dict, Tuple

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QCloseEvent, QResizeEvent
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QMainWindow, QVBoxLayout, QWidget

from intergrated_gui.frame_widget import FrameWidget
from intergrated_gui.information_widget import InformationWidget
from intergrated_gui.panel_widget import PanelWidget


class Window(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self._general_layout = QHBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)

        self._create_widgets()

        self._screen_size: QSize = QApplication.instance().primaryScreen().availableSize()
        # Limit the size to stay in comfort
        self.setMinimumSize(self._screen_size / 2)

    # Override
    def closeEvent(self, event: QCloseEvent) -> None:
        """A clean up function is called before closed if set."""
        # If there exists clean up callback, call it before passing the event
        # to the original implementation.
        if callable(getattr(self, "_clean_up_callback", False)):
            self._clean_up_callback()
        # Call the original implementation, which accepts and destroys the GUI
        # in default.
        super().closeEvent(event)
        # All other windows (no matter child or not) close with this window.
        QApplication.closeAllWindows()

    def set_clean_up_before_destroy(self, clean_up_callback: Callable[[], Any]) -> None:
        """Sets the clean up function to give the ability to do extra process
        before the GUI destroyed.

        Arguments:
            clean_up_callback: Is called before the GUI destroyed.
        """
        self._clean_up_callback = clean_up_callback

    # Override
    def resizeEvent(self, event: QResizeEvent) -> None:
        # The frame widget is shown only when the window is big enough;
        # otherwise hide it to keep the window clean.
        # (also prevents the frame from distortion under unbalanced window size)
        new_size = event.size()
        if (new_size.width() < self._screen_size.width() * 0.8
                or new_size.height() < self._screen_size.height() * 0.8):
            self.widgets["frame"].hide()
        else:
            self.widgets["frame"].show()
        # still the resize is allowed
        super().resizeEvent(event)

    def _create_widgets(self) -> None:
        """
        Information widget at the left-hand side, capture view in the middle,
        control panel at the right.
        """
        # The number is the stretch of the widget.
        widgets: Dict[str, Tuple[QWidget, int]] = {
            "information": (InformationWidget(), 1),
            "frame": (FrameWidget(), 2),
            "panel": (PanelWidget(), 1),
        }
        self.widgets: Dict[str, QWidget] = {}
        for name, (widget, stretch) in widgets.items():
            self.widgets[name] = widget
            self._general_layout.addWidget(widget, stretch=stretch)
