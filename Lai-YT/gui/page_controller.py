import os
from configparser import ConfigParser
from functools import partial

from PyQt5.QtGui import QDoubleValidator, QIntValidator


# Path of the config file.
CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")


class OptionController:
    """The OptionController handles the states of the OptionWidget,
    but it cares nothing about those which depends on others.
    """
    def __init__(self, option_widget, model, settings_check_callback, exit_callback):
        self._widget = option_widget
        self._model = model
        self._settings_check_callback = settings_check_callback
        self._exit_callback = exit_callback

        self._load_configs()
        self._enable_buttons()
        self._connect_actions()

    def _enable_buttons(self):
        """Set states of the action buttons."""
        # `Stop` is unabled at the beginning.
        self._widget.buttons["Stop"].setEnabled(False)
        # After being clicked, `Stop` is unables and `Start` is enabled.
        self._widget.buttons["Stop"].clicked.connect(
            lambda: self._widget.buttons["Stop"].setEnabled(False)
        )
        self._widget.buttons["Stop"].clicked.connect(
            lambda: self._widget.buttons["Start"].setEnabled(True)
        )

    def _connect_actions(self):
        """Connect the actions of the action buttons."""
        # Wiil do some verifications in click_start() before a real start.
        self._widget.buttons["Start"].clicked.connect(self._click_start)
        # `Stop` closes the application window.
        self._widget.buttons["Stop"].clicked.connect(self._model.close)
        # `Exit` closes both the application windows and GUI.
        self._widget.buttons["Exit"].clicked.connect(self._model.close)
        self._widget.buttons["Exit"].clicked.connect(self._exit_callback)
        # Also stores the GUI states back to the configuration file.
        self._widget.buttons["Exit"].clicked.connect(self._store_configs)

    def _click_start(self):
        """The Model starts if verifications are passed."""
        # To be able to do some verifications before a real start,
        # put all connections in another method instead of directly
        # connecting them.
        # After all verifications are passed, the start() method of Model is called.

        if self._settings_check_callback():
            # Now, all verifications are passed, the application is about to start.
            # Unable `Start` and enable `Stop`.
            self._widget.buttons["Start"].setEnabled(False)
            self._widget.buttons["Stop"].setEnabled(True)

            self._widget.message.clear()
            # Starts the application window.
            self._set_model_options()
            self._model.start()
        else:
            self._widget.message.setText("error: please make sure all settings are done")

    def _set_model_options(self):
        self._model.enable_distance_measure(self._widget.options["Distance Measure"].isChecked())
        self._model.enable_focus_time(self._widget.options["Focus Time"].isChecked())
        self._model.enable_posture_detect(self._widget.options["Posture Detect"].isChecked())

    def _load_configs(self):
        """Reads the previous state of check boxes and restore them."""
        config = ConfigParser()
        config.read(CONFIG)

        for opt_name, check_box in self._widget.options.items():
            check_box.setChecked(config.getboolean(opt_name, "checked"))

    def _store_configs(self):
        """Stores whether the check box is checked or not."""
        config = ConfigParser()
        config.read(CONFIG)

        for section, check_box in self._widget.options.items():
            config.set(section, "checked", 'True' if check_box.isChecked() else 'False')

        with open(CONFIG, 'w') as f:
            config.write(f)


class SettingController:
    """The SettingController handles the states of the SettingWidget,
    but it cares nothing about those which depends on others.
    """
    def __init__(self, setting_widget, model):
        self._widget = setting_widget
        self._model = model

        self._load_configs()
        self._set_valid_inputs()
        self._connect_actions()

    def _set_valid_inputs(self):
        """Set valid inputs of the settings."""
        # The user is still able to key in 00000~99999,
        # `intermediate` inputs will be found later at the button event stage
        # and error message will show.
        self._widget.settings["Face Width"].setPlaceholderText("5~24.99 (cm)")
        self._widget.settings["Face Width"].setValidator(QDoubleValidator(5, 24.99, 2))  # bottom, top, decimals
        self._widget.settings["Face Width"].setMaxLength(5)

        self._widget.settings["Distance"].setPlaceholderText("10~99.99 (cm)")
        self._widget.settings["Distance"].setValidator(QDoubleValidator(10, 99.99, 2))
        self._widget.settings["Distance"].setMaxLength(5)
    
    def _connect_actions(self):
        self._widget.save_button.clicked.connect(self._check_and_save)

    def _check_and_save(self):
        passed = self.check_inputs_validity()
        if passed:
            # Clear the message label to make sure no previous error.
            self._widget.message.clear()
            self._store_configs()
        else:
            self._widget.message.setText("error: parameter out of range")

    def check_inputs_validity(self):
        check_passed = True
        # When invalid parameter occurs, that parameter line is cleared.
        for parameter_line in self._widget.settings.values():
            if not parameter_line.hasAcceptableInput():
                check_passed = False
                parameter_line.clear()
        if check_passed:
            self._set_model_parameters()
            
        return check_passed

    def _load_configs(self):
        """If the user had set the parameters, restore them."""
        config = ConfigParser()
        config.read(CONFIG)

        for parameter, line_edit in self._widget.settings.items():
            if config.get("Distance Measure", parameter, fallback=None):
                line_edit.setText(config.get("Distance Measure", parameter))

    def _store_configs(self):
        """Only stores valid parameters.
        Empty input is also allowed, so users can clear by themselves.
        """
        config = ConfigParser()
        config.read(CONFIG)

        for parameter, line_edit in self._widget.settings.items():
            if line_edit.hasAcceptableInput() or line_edit.text() == "":
                config.set("Distance Measure", parameter, line_edit.text())
        
        with open(CONFIG, 'w') as f:
            config.write(f)

    def _set_model_parameters(self):
        self._model.set_face_width(float(self._widget.settings["Face Width"].text()))
        self._model.set_distance_to_camera(float(self._widget.settings["Distance"].text()))
