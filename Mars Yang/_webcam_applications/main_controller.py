import os
from configparser import ConfigParser
from functools import partial

from PyQt5.QtCore import QObject, QThread, pyqtSlot

from alpha import WebcamApplication
from gui.page_controller import OptionController, SettingController


#         Current controller hierarchy:
#
#                GuiController
#                      |
#                PageController (OptionController, SettingController)


class GuiController(QObject):
    """This is the main controller which controls the main GUI but not the individual Pages.
    Exceptions are the actions among pages and those depending on main GUI or app.
    """
    # Path of the config file.
    CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")

    def __init__(self, gui):
        super().__init__()
        # Extract the PageWidget to self._pages,
        # other common parts should be accessed through self._gui.
        self._pages = gui.page_widget.pages
        self._gui = gui

        self._create_page_controllers()
        self._load_page_configs()
        self._connect_signals_between_controller_and_gui()

    def _create_page_controllers(self):
        """Creates the controllers of the individual pages."""
        self._page_controllers = {
            "Options": OptionController(self._pages["Options"]),
            "Settings": SettingController(self._pages["Settings"]),
        }

    def _load_page_configs(self):
        """Loads the configs of each pages by delegating the real work to their own
        config loading method.
        """
        # Create a shared parser since they depends on the same config file.
        self._config = ConfigParser()
        self._config.read(GuiController.CONFIG)
        # Delegates the real work to their own config loading method.
        for controller in self._page_controllers.values():
            controller.load_configs(self._config)

    def _connect_signals_between_controller_and_gui(self):
        """Connect the siganls among widgets."""
        self._gui.destroyed.connect(self._store_page_configs)
        self._page_controllers["Options"].s_start.connect(self._start)
        self._page_controllers["Options"].s_exit.connect(self._gui.close)
        self._page_controllers["Settings"].s_save.connect(
            partial(self._page_controllers["Settings"].store_configs, self._config))

    @pyqtSlot()
    def _start(self):
        """Sets and starts the app.
        If no exception raised during the set, let OptionWidget know and start the app;
        otherwise start is discarded and error message shown at the OptionWidget.
        Also because the start() method of app is a long running loop, using QThread
        to prevent GUI from freezing.
        """
        # Shows a loading message to late user know we doing something.
        self._start_loading()
        # WebcamApplication is created every start to make able to moveToThread again and again.
        self._app = WebcamApplication()
        try:
            self._set_app_parameters()
        except ValueError:
            self._page_controllers["Options"].show_message("error: please make sure all settings are done")
            self._end_loading()
            return
        # Tell OptionController to react.
        self._page_controllers["Options"].successful_start()

        # Using QThread to prevent GUI from freezing.
        # Thread and App. are deleted after App. stops.
        self._thread = QThread()
        self._app.moveToThread(self._thread)
        self._thread.started.connect(self._app.start)
        self._app.s_stopped.connect(self._thread.quit)
        self._app.s_stopped.connect(self._app.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)
        self._connect_signals_between_controller_and_app()

        self._thread.start()

    def _start_loading(self):
        """Shows a loading message at the status bar (left corner)."""
        # Note that I've tried to addWidget() a QProgressBar to status bar,
        # but addWidget() seems to be slower than showMessage(),
        # which still makes the GUI freeze.
        self._gui.status_bar.showMessage("now loading...")

    def _end_loading(self):
        """Clears the loading message."""
        self._gui.status_bar.clearMessage()

    def _connect_signals_between_controller_and_app(self):
        # The s_start signal from app tells that the setups are done.
        self._app.s_started.connect(self._end_loading)
        # Change the ready flag of app to False, so the execution loop stops.
        self._page_controllers["Options"].s_stop.connect(self._close_app)
        self._page_controllers["Options"].s_exit.connect(self._close_app)

    @pyqtSlot()
    def _close_app(self):
        """Stops the execution loop of app by changing its flag."""
        self._app.ready = False

    def _set_app_parameters(self):
        """Passes the options state and settings to the app.
        Notice that the parameters are gotten from the ConfigParser, not the
        current SettingWidget. So it's save that invalid parameters won't be
        passed to the app (assume that only valid parameters are stored in the
        ConfigParser).
        """
        self._app.enable_distance_measure(
            enable=self._pages["Options"].options["Distance Measure"].isChecked(),
            face_width=self._config.getfloat("Distance Measure", "Face Width"),
            distance=self._config.getfloat("Distance Measure", "Distance"),
            warn_dist=self._config.getfloat("Distance Measure", "Bound"),)

        self._app.enable_focus_time(
            enable=self._pages["Options"].options["Focus Time"].isChecked(),
            time_limit=self._config.getint("Focus Time", "Time Limit"),
            break_time=self._config.getint("Focus Time", "Break Time"),)

        self._app.enable_posture_detect(
            enable=self._pages["Options"].options["Posture Detect"].isChecked(),
            warn_angle=self._config.getfloat("Posture Detect", "Angle"),)

    @pyqtSlot()
    def _store_page_configs(self):
        """Stores the configs of each pages by delegates the real work to their own
        config storing method.
        Except the SettingWidget since it's handled on its own.
        """
        # Delegates the real work to their own config loading method.
        for name, controller in self._page_controllers.items():
            if name not in {"Settings"}:
                controller.store_configs(self._config)
        # Save the states of all pages back to the config file all at once.
        with open(GuiController.CONFIG, 'w') as f:
            self._config.write(f)