from abc import ABC, abstractmethod
from configparser import ConfigParser
from functools import partial

from PyQt5.QtGui import QDoubleValidator, QIntValidator


class PageController(ABC):
    """The is a common interface of all PageControllers.
    A PageController should be able to have a load method and a store method,
    which do the action on their own page.
    """
    @abstractmethod
    def load_configs(self, config):
        """
        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        pass

    @abstractmethod
    def store_configs(self, config):
        """Notice that this method isn't aware of the file,
        which means it stores to the ConfigParser but not writes back to the config file.

        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        pass


class OptionController(PageController):
    """The OptionController handles the states of the OptionWidget,
    but it cares nothing about those which depends on others.
    """
    def __init__(self, option_widget):
        self._widget = option_widget

        self._enable_buttons()

    def successful_start(self):
        """Disable `Start` button and enable `Stop` button.
        Waits for the main controller to tell since we don't know whether the
        start succeeds or not at the first click.
        """
        # Clear possible error message from the last try.
        self._widget.message.clear()
        self._widget.buttons["Start"].setEnabled(False)
        self._widget.buttons["Stop"].setEnabled(True)

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

    def show_message(self, msg, color="red"):
        """Shows message at the message label of the OptionWidget.

        Arguments:
            msg (str): The message to show
            color (str): Color of the message. Default in red
        """
        self._widget.message.setText(msg)
        self._widget.message.set_color(color)

    def _enable_buttons(self):
        """Set the initial state of buttons.
        Since `Stop` always succeeds, we don't need another signal to tell.
        """
        # `Stop` is disabled at the beginning.
        self._widget.buttons["Stop"].setEnabled(False)
        # After being clicked, `Stop` is disables and `Start` is enabled.
        self._widget.buttons["Stop"].clicked.connect(
            lambda: self._widget.buttons["Stop"].setEnabled(False))
        self._widget.buttons["Stop"].clicked.connect(
            lambda: self._widget.buttons["Start"].setEnabled(True))


class SettingController(PageController):
    """The SettingController handles the states of the SettingWidget,
    but it cares nothing about those which depends on others.
    """
    def __init__(self, setting_widget):
        self._widget = setting_widget

        self._set_valid_inputs()
        self._connect_signals()

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

        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        for parameter, line_edit in self._widget.settings.items():
            if line_edit.hasAcceptableInput():
                config.set("Distance Measure", parameter, line_edit.text())

    def show_message(self, msg, color="red"):
        """Shows message at the message label of the SettingWidget.

        Arguments:
            msg (str): The message to show
            color (str): Color of the message. Default in red
        """
        self._widget.message.setText(msg)
        self._widget.message.set_color(color)

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

    def _connect_signals(self):
        # `Save` button connects to the double check method.
        self._widget.buttons["Save"].clicked.connect(self._save)
        # The message is cleared when any of the parameters are changed.
        for parameter_line in self._widget.settings.values():
            parameter_line.textChanged.connect(self._widget.message.clear)

    def _save(self):
        """This a button clicked double check method.
        If all the settings are valid, save them into config file and show a message;
        otherwise show an error and discard the click.
        """
        valid = self._check_inputs_validity()
        if valid:
            self.show_message("Saved!", "green")
            # Emits the signal to have the main controller call store_config
            # with the ConfigParser.
            self._widget.s_save.emit()
        else:
            self.show_message("Failed: parameter out of range", "red")

    def _check_inputs_validity(self):
       """Returns True if all parameters are in the range; otherwise clear the
       corresponding parameters and returns False.
       """
       check_passed = True
       for parameter_line in self._widget.settings.values():
           if not parameter_line.hasAcceptableInput():
               check_passed = False
               parameter_line.clear()

       return check_passed