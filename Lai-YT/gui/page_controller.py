import os
from configparser import ConfigParser

from PyQt5.QtGui import QDoubleValidator, QIntValidator


class PageController:
    """The PageController creates the controllers of the individual pages,
    Its only responsibility is to handle the actions "among" pages.
    States of a single page should be handled by their own controller.
    """
    # Path of the config file.
    CONFIG = os.path.join(os.path.abspath(os.path.dirname(__file__)), "gui_state.ini")

    def __init__(self, page_widget):
        """Access the individual pages by calling self._widget.pages["Options" | "Settings" | ...]."""
        self._widget = page_widget
        # Creates the controllers of the individual pages.
        self._page_controllers = {
            "Options": OptionController(self._widget.pages["Options"]),
            "Settings": SettingController(self._widget.pages["Settings"]),
        }
        # Load the configs of pages.
        self._load_configs()

    def _load_configs(self):
        """Loads the configs of each pages by delegates the real work to their own
        config loading method.
        """
        # Create a shared parser since they depends on the same config file.
        config = ConfigParser()
        config.read(PageController.CONFIG)
        # Delegates the real work to their own config loading method.
        for controller in self._page_controllers.values():
            controller.load_configs(config)

    def store_configs(self):
        """Stores the configs of each pages by delegates the real work to their own
        config storing method.
        """
        # Create a shared parser since they depends on the same config file.
        config = ConfigParser()
        config.read(PageController.CONFIG)
        # delegates the real work to their own
        # config storing method.
        for controller in self._page_controllers.values():
            controller.store_configs(config)
        # Save the states of all pages back to the config file all in once.
        with open(PageController.CONFIG, 'w') as f:
            config.write(f)

    def check_inputs_validity(self):
        """Returns True if option `Distance Measure` is unchecked or all parameters it needs is in the range.
        The invalid parameters is cleared during the check. Error message is cleared is check passed.
        """
        check_passed = True
        if self._widget.pages["Options"].options["Distance Measure"].isChecked():
            # When invalid parameter occurs, that parameter line is cleared
            # and the error message shown after the option `Distance Measure`.
            for parameter_line in self._widget.pages["Settings"].settings.values():
                if not parameter_line.hasAcceptableInput():
                    check_passed = False
                    parameter_line.clear()
                    self._widget.pages["Options"].messages["Distance Measure"].setText("error: parameter out of range")

        if check_passed:
            # Clear the message label to make sure no previous error.
            self._widget.pages["Options"].messages["Distance Measure"].clear()

        return check_passed

    def set_model_parameters(self, model):
        """Passes the options state and settings to model.

        Arguments:
            model (WebcamApplication): The model has the core algorithm.
        """
        model.enable_focus_time(self._widget.pages["Options"].options["Focus Time"].isChecked())
        model.enable_posture_detect(self._widget.pages["Options"].options["Posture Detect"].isChecked())
        # Parameters are replaced by 0 if `Distance Measure` aren't selected.
        if self._widget.pages["Options"].options["Distance Measure"].isChecked():
            model.enable_distance_measure(
                True,
                face_width=float(self._widget.pages["Settings"].settings["Face Width"].text()),
                distance=float(self._widget.pages["Settings"].settings["Distance"].text())
            )
        else:
            model.enable_distance_measure(False, 0, 0)


class OptionController:
    """The OptionController handles the states of the OptionWidget,
    but it cares nothing about those which depends on others.
    """
    def __init__(self, option_widget):
        self._widget = option_widget

    def load_configs(self, config):
        """Reads the previous state of check boxes and restore them.

        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        for opt_name, check_box in self._widget.options.items():
            check_box.setChecked(config.getboolean(opt_name, "checked"))

    def store_configs(self, config):
        """Stores whether the check box is checked or not.

        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        for section, check_box in self._widget.options.items():
            config.set(section, "checked", 'True' if check_box.isChecked() else 'False')


class SettingController:
    """The SettingController handles the states of the SettingWidget,
    but it cares nothing about those which depends on others.
    """
    def __init__(self, setting_widget):
        self._widget = setting_widget

        self._set_valid_inputs()

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

    def load_configs(self, config):
        """If the user had set the parameters, restore them.

        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        for parameter, line_edit in self._widget.settings.items():
            if config.get("Distance Measure", parameter, fallback=None):
                line_edit.setText(config.get("Distance Measure", parameter))

    def store_configs(self, config):
        """Only stores valid parameters.
        Empty input is also allowed, so users can clear by themselves.

        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        for parameter, line_edit in self._widget.settings.items():
            if line_edit.hasAcceptableInput() or line_edit.text() == "":
                config.set("Distance Measure", parameter, line_edit.text())
