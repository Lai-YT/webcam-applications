import os
from configparser import ConfigParser

from PyQt5.QtGui import QDoubleValidator, QIntValidator

from gui.view import ApplicationGui


# Controller handles the states of GUI's components,
# extracts the inputs from users and pass them to Model.
class GuiController:
    # Path of the config file.
    CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")

    def __init__(self, model, gui):
        self._model = model
        self._gui = gui

        # self._set_input_locks()
        self._load_configs()
        self._enable_buttons()
        self._connect_actions()

    def _load_configs(self):
        config = ConfigParser()
        config.read(GuiController.CONFIG)
        # Read the previous state of check boxes and restore them.
        for opt_name, check_box in self._gui.options.items():
            check_box.setChecked(config.getboolean(opt_name, "checked"))

    def _store_configs(self):
        """Stores the state of the current GUI."""
        config = ConfigParser()
        config.read(GuiController.CONFIG)
        # Stores whether the check box is checked or not.
        for section, check_box in self._gui.options.items():
            config.set(section, "checked", 'True' if check_box.isChecked() else 'False')
        # Save the states back to the config file.
        with open(GuiController.CONFIG, 'w') as f:
            config.write(f)

    def _enable_buttons(self):
        """Set states of the action buttons."""
        # `Stop` is unabled at the beginning.
        self._gui.action_buttons["Stop"].setEnabled(False)
        # After being clicked, `Stop` is unables and `Start` is enabled.
        self._gui.action_buttons["Stop"].clicked.connect(
            lambda: self._gui.action_buttons["Stop"].setEnabled(False)
        )
        self._gui.action_buttons["Stop"].clicked.connect(
            lambda: self._gui.action_buttons["Start"].setEnabled(True)
        )

    def _connect_actions(self):
        # Wiil do some verifications in click_start() before a real start.
        self._gui.action_buttons["Start"].clicked.connect(self._click_start)
        # `Stop` closes the application window.
        self._gui.action_buttons["Stop"].clicked.connect(self._model.close)
        # `Exit` closes both the application windows and GUI.
        self._gui.action_buttons["Exit"].clicked.connect(self._model.close)
        self._gui.action_buttons["Exit"].clicked.connect(self._gui.close)
        # Also stores the GUI states back to the configuration file.
        self._gui.action_buttons["Exit"].clicked.connect(self._store_configs)
        #
        self._gui.action_buttons["Settings"].clicked.connect(self._call_settings)

    def _click_start(self):
        """The Model starts if verifications are passed."""
        # To be able to do some verifications before a real start,
        # put all connections in another method instead of directly
        # connecting them.
        # After all verifications are passed, the start() method of Model is called.

        # If `Distance Measure` is selected, check if all parameters are valid.
        if self._gui.options["Distance Measure"].isChecked():
            if not self._check_inputs_validity():
                return

        # Now, all verifications are passed, the application is about to start.
        # Unable `Start` and enable `Stop`.
        self._gui.action_buttons["Start"].setEnabled(False)
        self._gui.action_buttons["Stop"].setEnabled(True)
        # Starts the application window.
        self._set_model_parameters()
        self._model.start()
    
    def _call_settings(self):
        import sys

        from PyQt5.QtWidgets import QApplication

        from alpha import WebcamApplication
        from gui.settings_controller import SettingsController
        from gui.settings import SettingsGui

        settings = QApplication(sys.argv)
        # Create the settings GUI.
        print("a")
        settings_gui = SettingsGui()
        print("b")
        settings_gui.show()
        # Take control of the GUI and the Application.
        print("c")
        settings_controller = SettingsController(model=WebcamApplication(), gui=settings_gui)
        print("d")
        # Execute the event loop.
        sys.exit(settings.exec())
