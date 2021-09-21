import time
from abc import abstractmethod
from functools import partial
from math import ceil

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QDoubleValidator, QIntValidator

from gui.page_widget import TrainingDialog
from gui.task_worker import TaskWorker
from lib.train import PostureLabel, ModelTrainer


class PageController(QObject):
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

    """Hide the concrete widget. Communicate with main controller through signals."""
    s_start = pyqtSignal()
    s_stop = pyqtSignal()
    s_exit = pyqtSignal()

    def __init__(self, option_widget):
        super().__init__()

        self._widget = option_widget

        self._enable_buttons()
        self._connect_signals()

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

    def _connect_signals(self):
        """Connect the buttons to signals."""
        self._widget.buttons["Start"].clicked.connect(self.s_start)
        self._widget.buttons["Stop"].clicked.connect(self.s_stop)
        self._widget.buttons["Exit"].clicked.connect(self.s_exit)


class SettingController(PageController):
    """The SettingController handles the states of the SettingWidget,
    but it cares nothing about those which depends on others.
    """

    """Hide the concrete widget. Communicate with main controller through signals."""
    s_save = pyqtSignal()

    def __init__(self, setting_widget):
        super().__init__()

        self._widget = setting_widget

        self._set_valid_inputs()
        self._connect_signals()

    def load_configs(self, config):
        """If the user had set the parameters, restore them.

        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        for option, parameters in self._widget.settings.items():
            for name, line in parameters.items():
                line.setText(config.get(option, name))

    def store_configs(self, config):
        """Only stores valid parameters.

        Arguments:
            config (ConfigParser): The parser which reads the config file
        """
        for option, parameters in self._widget.settings.items():
            for name, line in parameters.items():
                if line.hasAcceptableInput():
                    config.set(option, name, line.text())

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
        self._widget.settings["Distance Measure"]["Face Width"].setPlaceholderText("5 ~ 24.99 (cm)")
        self._widget.settings["Distance Measure"]["Face Width"].setValidator(QDoubleValidator(5, 24.99, 2))  # bottom, top, decimals
        self._widget.settings["Distance Measure"]["Face Width"].setMaxLength(5)

        self._widget.settings["Distance Measure"]["Distance"].setPlaceholderText("10 ~ 99.99 (cm)")
        self._widget.settings["Distance Measure"]["Distance"].setValidator(QDoubleValidator(10, 99.99, 2))
        self._widget.settings["Distance Measure"]["Distance"].setMaxLength(5)

        self._widget.settings["Distance Measure"]["Bound"].setPlaceholderText("30 ~ 59.99 (cm)")
        self._widget.settings["Distance Measure"]["Bound"].setValidator(QDoubleValidator(30, 59.99, 2))
        self._widget.settings["Distance Measure"]["Bound"].setMaxLength(5)

        self._widget.settings["Focus Time"]["Time Limit"].setPlaceholderText("1 ~ 59 (min)")
        self._widget.settings["Focus Time"]["Time Limit"].setValidator(QIntValidator(1, 59))

        self._widget.settings["Focus Time"]["Break Time"].setPlaceholderText("1 ~ 59 (min)")
        self._widget.settings["Focus Time"]["Break Time"].setValidator(QIntValidator(1, 59))

        self._widget.settings["Posture Detect"]["Angle"].setPlaceholderText("5 ~ 24.99 (deg)")
        self._widget.settings["Posture Detect"]["Angle"].setValidator(QDoubleValidator(5, 25, 2))
        self._widget.settings["Posture Detect"]["Angle"].setMaxLength(5)

    def _connect_signals(self):
        # `Save` button connects to the double check method.
        self._widget.buttons["Save"].clicked.connect(self._save)
        # The message is cleared when any of the parameters are changed.
        for parameters in self._widget.settings.values():
            for parameter_line in parameters.values():
                parameter_line.textChanged.connect(self._widget.message.clear)

    @pyqtSlot()
    def _save(self):
        """This a button clicked double check method.
        If all the settings are valid, save them into config file and show a message;
        otherwise show an error and discard the click.
        """
        valid = self._check_inputs_validity()
        if valid:
            self.show_message("Saved!", "green")
            # Emits the signal to have the main controller call store_configs
            # with the ConfigParser.
            self.s_save.emit()
        else:
            self.show_message("Failed: parameter out of range", "red")

    def _check_inputs_validity(self):
       """Returns True if all parameters are in the range; otherwise clear the
       corresponding parameters and returns False.
       """
       check_passed = True
       for parameters in self._widget.settings.values():
           for parameter_line in parameters.values():
               if not parameter_line.hasAcceptableInput():
                   check_passed = False
                   parameter_line.clear()

       return check_passed


class ModelController(PageController):
    def __init__(self, model_widget):
        super().__init__()
        self._widget = model_widget
        self._model_trainer = ModelTrainer()

        self._enable_buttons()
        self._connect_signals()
        self._connect_buttons()

    def load_configs(self, config):
        pass

    def store_configs(self, config):
        pass

    @pyqtSlot()
    def _train_model(self):
        self._worker = TaskWorker(self._model_trainer.train_model)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)

        # The worker starts running the task when the thread starts.
        self._thread.started.connect(self._worker.run)
        # The thread deletes when it's finished.
        self._thread.finished.connect(self._thread.deleteLater)
        # The thread is finished when the worker task is finished.
        self._worker.s_finished.connect(self._thread.quit)
        # The worker deletes when it's finished.
        self._worker.s_finished.connect(self._worker.deleteLater)
        # Quit countdown when training is finished.
        self._model_trainer.s_train_finished.connect(self._quit_countdown)

        # All connections are ready. let's start!
        self._thread.start()

        self._countdown()

    def _enable_buttons(self):
        # Capture and Finish is disabled at the beginning.
        self._widget.buttons["Capture"].setEnabled(False)
        self._widget.buttons["Finish"].setEnabled(False)
        # Capture is enabled after any of the option buttons is toggled.
        for opt_btn in self._widget.options.values():
            opt_btn.toggled.connect(lambda: self._widget.buttons["Capture"].setEnabled(True))
        # `Finish` is the only button can click during capture.
        self._widget.buttons["Capture"].clicked.connect(
            lambda: self._widget.buttons["Finish"].setEnabled(True))
        self._widget.buttons["Capture"].clicked.connect(
            lambda: self._widget.buttons["Capture"].setEnabled(False))
        self._widget.buttons["Capture"].clicked.connect(
            lambda: self._widget.buttons["Train"].setEnabled(False))
        # If is not capturing, `Capture` and `Train` can be clicked.
        self._widget.buttons["Finish"].clicked.connect(
            lambda: self._widget.buttons["Capture"].setEnabled(True))
        self._widget.buttons["Finish"].clicked.connect(
            lambda: self._widget.buttons["Finish"].setEnabled(False))
        self._widget.buttons["Finish"].clicked.connect(
            lambda: self._widget.buttons["Train"].setEnabled(True))

        self._widget.buttons["Train"].clicked.connect(
            lambda: self._widget.buttons["Finish"].setEnabled(False))
        self._widget.buttons["Train"].clicked.connect(
            lambda: self._widget.buttons["Train"].setEnabled(False))

    def _connect_buttons(self):
        # Notice that the clicked signal also passes an argument: False (False because uncheckable).
        # If the slot function takes any parameter, make sure you handle the effect.
        # e.g, use pyqtSlot decorator or connect with lambda.
        self._widget.buttons["Train"].clicked.connect(self._train_model)
        self._widget.buttons["Capture"].clicked.connect(self._capture_sampe_images)
        self._widget.buttons["Finish"].clicked.connect(self._model_trainer.stop_capturing)

    def _connect_signals(self):
        # The `Train` button is enabled after the previous training is finished.
        self._model_trainer.s_train_finished.connect(
            lambda: self._widget.buttons["Train"].setEnabled(True))

    def _capture_sampe_images(self):
        selected_option = self._widget.option_ids[self._widget.options_group.checkedId()]
        if selected_option == "Good":
            self._model_trainer.capture_sample_images(PostureLabel.good)
        elif selected_option == "Slump":
            self._model_trainer.capture_sample_images(PostureLabel.slump)

    def _countdown(self):
        """Countdown when training to let user know how much time left."""
        self._countdown_flag = False

        image_count = sum(self._model_trainer.get_image_count().values())
        # The following formula is the time that training takes.
        self.estimated_training_time: int = 10 * (1 + 3 * image_count // 100)

        if not hasattr(self, "_progress_dialog"):
            # Since the TrainingDialog is modal (lock parent widget), setting parent
            # is necessary.
            self._progress_dialog = TrainingDialog(self.estimated_training_time, parent=self._widget)
        else:
            self._progress_dialog.setMaximum(self.estimated_training_time)

        # Run the for loop one time less than max to avoid reaching max.
        for count in range(self.estimated_training_time):
            # If flag is True, leave the function so the progress bar will stop.
            if self._countdown_flag:
                return
            # countdown process
            self._progress_dialog.setLabelText(
                f"{ceil((self.estimated_training_time - count) / 60)} minute(s) left...")
            self._progress_dialog.setValue(count)
            time.sleep(1)
        # If training is not finished, lock the bar value and display the waiting message.
        self._progress_dialog.setLabelText("Soon be finished...")

    def _quit_countdown(self):
        """Set bar value to max to close the countdown dialog."""
        self._countdown_flag = True
        self._progress_dialog.setValue(self.estimated_training_time)
