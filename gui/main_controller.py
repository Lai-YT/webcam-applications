import os
from configparser import ConfigParser
from functools import partial

from PyQt5.QtCore import QObject, QThread, pyqtSlot

from gui.page_controller import OptionController, SettingController, ModelController
from intergrated_gui.component import FailMessageBox
from posture.train import ModelPath
from util.task_worker import TaskWorker


#               Controller hierarchy:
#
#                GuiController - ApplicationGui, WebcamApplication
#                      |
#                PageController (OptionController, SettingController, ...)


class GuiController(QObject):
    """This is the main controller which controls the main GUI but not the individual Pages.
    Exceptions are the actions among pages and those depending on main GUI or app.
    """
    # Path of the config file.
    CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")

    def __init__(self, gui, application):
        super().__init__()
        # Extract the PageWidget to self._pages,
        # other common parts should be accessed through self._gui.
        self._pages = gui.page_widget.pages
        self._gui = gui
        self._app = application

        self._create_page_controllers()
        self._load_page_configs()
        self._connect_signals_between_controller_and_gui()
        self._connect_signals_between_controller_and_app()

    def _create_page_controllers(self):
        """Creates the controllers of the individual pages."""
        self._page_controllers = {
            "Options": OptionController(self._pages["Options"]),
            "Settings": SettingController(self._pages["Settings"]),
            "Model": ModelController(self._pages["Model"]),
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
        # Have the configs save before GUI being destroyed.
        self._gui.set_clean_up_before_destroy(self._store_page_configs)
        # Starts the app after some preceding processes.
        self._page_controllers["Options"].s_start.connect(self._start)

        self._page_controllers["Options"].s_exit.connect(self._gui.close)
        # Passes the configparser to `Settings` to have it handle its own storing process.
        self._page_controllers["Settings"].s_save.connect(
            partial(self._page_controllers["Settings"].store_configs, self._config))

    def _connect_signals_between_controller_and_app(self):
        # The s_start signal from app tells that the setups are done.
        self._app.s_started.connect(self._end_loading)
        # Change the ready flag of app to False, so the execution loop stops.
        self._page_controllers["Options"].s_stop.connect(self._app.stop)
        self._page_controllers["Options"].s_exit.connect(self._app.stop)

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

        try:
            self._set_app_parameters()
        except ValueError:
            self._page_controllers["Options"].show_message("error: please make sure all settings are done")
            self._end_loading()
            return
        except FileNotFoundError as e:
            self._page_controllers["Options"].show_message(str(e))
            self._end_loading()
            return

        # Tell OptionController to react.
        self._page_controllers["Options"].successful_start()

        # Using QThread to prevent GUI from freezing.
        # The TaskWorker let us only move the start method into thread,
        # so the App. itself is reusable.
        self._worker = TaskWorker(self._app.start)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        # Worker starts running after the thread is started.
        self._thread.started.connect(self._worker.run)
        # The job of thread and worker is finished after the App. calls stop.
        self._app.s_stopped.connect(self._thread.quit)
        self._app.s_stopped.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

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

    def _set_app_parameters(self):
        """Passes the options state and settings to the app.
        Notice that the parameters are gotten from the ConfigParser, not the
        current SettingWidget. So it's save that invalid parameters won't be
        passed to the app (assume that only valid parameters are stored in the
        ConfigParser).
        """
        self._app.enable_distance_measure(
            enable=self._pages["Options"].options["Distance Measure"].isChecked(),
            distance=self._config.getfloat("Distance Measure", "Distance"),
            warn_dist=self._config.getfloat("Distance Measure", "Bound"))

        self._app.enable_focus_time(
            enable=self._pages["Options"].options["Focus Time"].isChecked(),
            time_limit=self._config.getint("Focus Time", "Time Limit"),
            break_time=self._config.getint("Focus Time", "Break Time"))

        # Get which model to use and sent it to the app.
        # If is a custom model, also checks the existence. Inform ths user and abort
        # the `start` if doesn't exist.
        selected_model_name = self._page_controllers["Options"].get_selected_model_name()
        if selected_model_name == "Default":
            model_path = ModelPath.DEFAULT
        elif selected_model_name == "Custom":
            model_path = ModelPath.CUSTOM
            if not os.path.isfile(model_path.value):
                FailMessageBox("Please train the custom model first.").exec()
                raise FileNotFoundError("error: please train the custom model first")

        self._app.enable_posture_detect(
            enable=self._pages["Options"].options["Posture Detect"].isChecked(),
            model_path=model_path,
            warn_angle=self._config.getfloat("Posture Detect", "Angle"))

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
        with open(GuiController.CONFIG, "w") as f:
            self._config.write(f)
