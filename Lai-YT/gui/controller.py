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

        self._set_valid_inputs()
        self._set_input_locks()
        self._load_configs()
        self._enable_buttons()
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
        config.read(GuiController.CONFIG)
        # Read the previous state of check boxes and restore them.
        for opt_name, check_box in self._gui.options.items():
            check_box.setChecked(config.getboolean(opt_name, "checked"))
        # If the user had set the parameters, restore them.
        for parameter, line_edit in self._gui.settings.items():
            if config.get("Distance Measure", parameter, fallback=None):
                line_edit.setText(config.get("Distance Measure", parameter))

    def _store_configs(self):
        """Stores the state of the current GUI."""
        config = ConfigParser()
        config.read(GuiController.CONFIG)
        # Stores whether the check box is checked or not.
        for section, check_box in self._gui.options.items():
            config.set(section, "checked", 'True' if check_box.isChecked() else 'False')
        # `Distance Measure`: only stores valid parameters.
        # Empty input is also allowed, so users can clear by themselves.
        for parameter, line_edit in self._gui.settings.items():
            if line_edit.hasAcceptableInput() or line_edit.text() == "":
                config.set("Distance Measure", parameter, line_edit.text())
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

    def _set_input_locks(self):
        """If `Distance Measure` is not checked, lock the entries to avoid unnecessary parameters."""
        self._gui.options["Distance Measure"].toggled.connect(lambda checked: self._lock_inputs(not checked))

    def _lock_inputs(self, status: bool):
        """Show gray and read-only parameters when locked, otherwise black, as normal."""
        for parameter in self._gui.settings.values():
            if status:
                parameter.set_color("gray")
                parameter.setReadOnly(True)
            else:
                parameter.set_color("black")
                parameter.setReadOnly(False)
