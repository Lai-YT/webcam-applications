from typing import Any, Callable, Dict, Optional, Tuple

from PyQt5.QtCore import QSize, Qt
from PyQt5.QtGui import QCloseEvent, QIcon, QResizeEvent
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QMainWindow,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

import gui.img.icon
from gui.frame_widget import FrameWidget
from gui.information_widget import InformationWidget
from gui.language import LanguageWidget
from gui.panel_widget import PanelWidget


class Window(QMainWindow):
    """The main GUI view of the applications."""
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Webcam application")
        self.setWindowIcon(QIcon(":webcam.ico"))

        self._general_layout = QHBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)
        self._create_widgets()

        self._set_minimum_window_size()

        self._clean_up_callback: Optional[Callable[[], Any]] = None

    def _set_minimum_window_size(self) -> None:
        self._screen_size: QSize = QApplication.instance().primaryScreen().availableSize()
        # Limit the size to stay in comfort
        self.setMinimumSize(self._screen_size / 2)

    # Override
    def closeEvent(self, event: QCloseEvent) -> None:
        """A clean up function is called before closed if set."""
        # If there exists clean up callback, call it before passing the event
        # to the original implementation.
        if self._clean_up_callback is not None:
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
        new_size: QSize = event.size()
        if (new_size.width() < self._screen_size.width() * 0.8
                or new_size.height() < self._screen_size.height() * 0.8):
            self.widgets["frame"].hide()
        else:
            self.widgets["frame"].show()
        # still the resize is allowed
        super().resizeEvent(event)

    def _create_widgets(self) -> None:
        """Creates information widget at the left-hand side, capture view in the
        middle, control panel at the right.
        """
        self.widgets: Dict[str, QWidget] = {}
        self._create_info_and_lang_widget()

        # The number is the stretch of the widget.
        widgets: Dict[str, Tuple[QWidget, int]] = {
            "frame": (FrameWidget(), 2),
            "panel": (PanelWidget(), 1),
        }

        for name, (widget, stretch) in widgets.items():
            self.widgets[name] = widget
            self._general_layout.addWidget(widget, stretch=stretch)

        self._make_panel_widget_scrollable()

    def _create_info_and_lang_widget(self) -> None:
        """Creates information widget at the left-hand side with language widget under."""
        info_and_lang_layout = QVBoxLayout()

        self.widgets["information"] = InformationWidget()
        self.widgets["language"] = LanguageWidget()

        # add both of them, information should occupy more space
        info_and_lang_layout.addWidget(self.widgets["information"], stretch=5)
        info_and_lang_layout.addWidget(
            self.widgets["language"], stretch=1, alignment=Qt.AlignBottom)

        self._general_layout.insertLayout(0, info_and_lang_layout, stretch=1)

    def _make_panel_widget_scrollable(self) -> None:
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.widgets["panel"])
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._general_layout.addWidget(scroll_area)
