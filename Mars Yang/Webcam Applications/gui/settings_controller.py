import os
from configparser import ConfigParser

from PyQt5.QtGui import QDoubleValidator, QIntValidator

from gui.view import ApplicationGui
from gui.settings import SettingsGui


# Controller handles the states of GUI's components,
# extracts the inputs from users and pass them to Model.
class SettingsController:
    # Path of the config file.
    CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")

    def __init__(self, model, gui):
        self._model = model
        self._gui = gui

        self._set_valid_inputs()
        self._load_configs()
        self._connect_actions()

    def _set_valid_inputs(self):
        """Set valid inputs of the settings."""
        # The user is still able to key in 00000~99999,
        # `intermediate` inputs will be found later at the button event stage
        # and error message will show.
        self._gui.settings["Face Width"].setPlaceholderText("5~24.99 (cm)")
        self._gui.settings["Face Width"].setValidator(QDoubleValidator(5, 24.99, 2))  # bottom, top, decimals
        self._gui.settings["Face Width"].setMaxLength(5)

        self._gui.settings["Distance"].setPlaceholderText("10~99.99 (cm)")
        self._gui.settings["Distance"].setValidator(QDoubleValidator(10, 99.99, 2))
        self._gui.settings["Distance"].setMaxLength(5)

    def _load_configs(self):
        config = ConfigParser()
        config.read(SettingsController.CONFIG)
        # If 'Distance Measure' is unchecked, lock inputs beforehand.
        self._lock_inputs(not self._gui.options["Distance Measure"].isChecked())
        # If the user had set the parameters, restore them.
        for parameter, line_edit in self._gui.settings.items():
            if config.get("Distance Measure", parameter, fallback=None):
                line_edit.setText(config.get("Distance Measure", parameter))

    def _store_configs(self):
        """Stores the state of the current GUI."""
        config = ConfigParser()
        config.read(SettingsController.CONFIG)
        # `Distance Measure`: only stores valid parameters.
        # Empty input is also allowed, so users can clear by themselves.
        for parameter, line_edit in self._gui.settings.items():
            if line_edit.hasAcceptableInput() or line_edit.text() == "":
                config.set("Distance Measure", parameter, line_edit.text())
        # Save the states back to the config file.
        with open(SettingsController.CONFIG, 'w') as f:
            config.write(f)

    def _connect_actions(self):
        # 
        self._gui.action_buttons["Confirm"].clicked.connect(self._click_start)

    def _click_start(self):
        """The Model starts if verifications are passed."""
        # To be able to do some verifications before a real start,
        # put all connections in another method instead of directly
        # connecting them.
        # After all verifications are passed, the start() method of Model is called.

        # If `Distance Measure` is selected, check if all parameters are valid.
        if not self._check_inputs_validity():
            return
        else:
            self._gui.close()
            
        # Starts the application window.
        self._set_model_parameters()

    def _check_inputs_validity(self):
        """Returns True if all parameters that Distance Measure needs is in the range."""
        check_passed = True
        # When invalid parameter occurs, that parameter line is cleared
        # and the error message shown after the option `Distance Measure`.
        for parameter_line in self._gui.settings.values():
            if not parameter_line.hasAcceptableInput():
                check_passed = False
                parameter_line.clear()
                self._gui.option_msgs["Distance Measure"].setText("error: parameter out of range")

        if check_passed:
            # Clear the message label to make sure no previous error.
            self._gui.option_msgs["Distance Measure"].clear()

        return check_passed

    def _set_model_parameters(self):
        """Pass the options and parameters to Model in accordance with the GUI state."""
        self._model.enable_focus_time(self._gui.options["Focus Time"].isChecked())
        self._model.enable_posture_detect(self._gui.options["Posture Detect"].isChecked())
        # Parameters are replaced by 0 if `Distance Measure` aren't selected.
        if self._gui.options["Distance Measure"].isChecked():
            self._model.enable_distance_measure(
                True,
                face_width=float(self._gui.settings["Face Width"].text()),
                distance=float(self._gui.settings["Distance"].text())
            )
        else:
            self._model.enable_distance_measure(False, 0, 0)

