import os
from configparser import ConfigParser
from functools import partial

from gui.page_controller import OptionController, SettingController


#         Current controller hierarchy:
#
#                GuiController
#                      |
#                PageController (OptionController, SettingController)


class GuiController:
    """This is the main controller which controls the main GUI but not the individual Pages.
    Exceptions are the actions among pages and those depending on main GUI or app.
    """
    # Path of the config file.
    CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")

    def __init__(self, app, gui):
        # app has the core algorithm.
        self._app = app
        # Extract the PageWidget to self._pages,
        # other common parts should be accessed through self._gui.
        self._pages = gui.page_widget.pages
        self._gui = gui

        self._create_page_controllers()
        self._load_page_configs()
        self._connect_signals()

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

    def _connect_signals(self):
        """Connect the siganls among widgets."""
        # --- main GUI ---
        # Stores the state of widgets when the GUI is closed (by `Exit` or `X`).
        self._gui.destroyed.connect(self._store_page_configs)

        # --- OptionWidget ---
        # Do some extra process and checks before a real start.
        self._pages["Options"].s_start.connect(self._start)
        # `Stop` closes the application window.
        self._pages["Options"].buttons["Stop"].clicked.connect(self._app.close)
        # `Exit` closes both the application windows and GUI.
        self._pages["Options"].buttons["Exit"].clicked.connect(self._app.close)
        self._pages["Options"].buttons["Exit"].clicked.connect(self._gui.close)

        # --- SettingWidget ---
        # When `Save` is clicked successfully, store the state with config.
        self._pages["Settings"].s_save.connect(
            partial(self._page_controllers["Settings"].store_configs, self._config))

    def _start(self):
        """Sets and starts the app.
        If no exception raised during the set, let OptionWidget know and start the app;
        otherwise start is discarded and error message shown at the OptionWidget.
        """
        try:
            self._set_app_parameters()
        except ValueError:
            self._page_controllers["Options"].show_message("error: please make sure all settings are done")
            return

        self._page_controllers["Options"].successful_start()
        # Starts the application window.
        self._app.start()

    def _set_app_parameters(self):
        """Passes the options state and settings to the app.
        Notice that the parameters are gotten from the ConfigParser, not the
        current SettingWidget. So it's save that invalid parameters won't be
        passed to the app (assume that only valid parameters are stored in the
        ConfigParser)
        """
        self._app.enable_focus_time(self._pages["Options"].options["Focus Time"].isChecked())
        self._app.enable_posture_detect(self._pages["Options"].options["Posture Detect"].isChecked())
        # Parameters are replaced by 0 if `Distance Measure` aren't selected.
        if self._pages["Options"].options["Distance Measure"].isChecked():
            self._app.enable_distance_measure(
                True,
                face_width=self._config.getfloat("Distance Measure", "Face Width"),
                distance=self._config.getfloat("Distance Measure", "Distance")
            )
        else:
            self._app.enable_distance_measure(False, 0, 0)

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
