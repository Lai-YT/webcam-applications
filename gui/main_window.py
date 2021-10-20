from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget

import gui.img.icon
from gui.component import StatusBar
from gui.page_widget import PageWidget


#     GUI layout:
#    -----------------------
#    | ------------------- | <- Central Widegt is a pure QWidget.
#    | |                 | <- General Layout margin of the Main GUI.
#    | |                 | |
#    | |      Pages  <- Created by PageWidget (OptionWidget, SettingWidget, ...).
#    | |                 | |
#    | |                 | |
#    | ------------------- |
#    | status bar          |
#    -----------------------


class ApplicationGui(QMainWindow):
    """This is the pure GUI part, provides no functionalitiy.
    Its responsibility is to create all components the GUI should have,
    which means no other components will be added by other parts (Controller, App).
    Functionality of the components are set by the Controllers.
    """

    def __init__(self):
        super().__init__()
        # Set some main window's properties.
        self.setWindowTitle("Webcam application")
        self.setWindowIcon(QIcon(":webcam.ico"))
        self.setFixedSize(500, 450)
        # Set the central widget and the general layout.
        self._general_layout = QVBoxLayout()
        self._central_widget = QWidget()
        self._central_widget.setLayout(self._general_layout)
        self.setCentralWidget(self._central_widget)

        self._create_status_bar()
        # Top is the page area.
        self._create_pages()

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
        # All other windows (no matter child or not) close with this window.
        QApplication.closeAllWindows()

    def set_clean_up_before_destroy(self, clean_up_callback):
        """Sets the clean up function to give the ability to do extra process
        before the GUI destroyed.

        Arguments:
            clean_up_callback (Callable[[], Any]): Is called before the GUI destroyed
        """
        self._clean_up_callback = clean_up_callback

    def _create_status_bar(self):
        self.status_bar = StatusBar()
        self.setStatusBar(self.status_bar)

    def _create_pages(self):
        """Creates the page area. Components are created by PageWidget."""
        self.page_widget = PageWidget()
        self._general_layout.addWidget(self.page_widget)
