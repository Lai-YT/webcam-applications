from PyQt5.QtGui import QDoubleValidator, QIntValidator

from gui.view import ApplicationGui


# Controller handles the states of GUI's components,
# extract the inputs from users and pass them to Model.
class GuiController:
    def __init__(self, model, gui):
        self._model = model
        self._gui = gui

        self._set_valid_inputs()
        self._enable_buttons()
        self._connect_actions()

    def _set_valid_inputs(self):
        """Set valid inputs of the settings."""
        # The user is still able to key in 00000~99999,
        # `intermediate` inputs will be found at the button event stage
        # and error message will shown.
        self._gui.settings["Face Width"].set_placeholder_text("5~24.99 (cm)")
        self._gui.settings["Face Width"].setValidator(QDoubleValidator(5, 24.99, 2))  # bottom, top, decimals
        self._gui.settings["Face Width"].setMaxLength(5)

        self._gui.settings["Distance"].set_placeholder_text("10~99.99 (cm)")
        self._gui.settings["Distance"].setValidator(QDoubleValidator(10, 99.99, 2))
        self._gui.settings["Distance"].setMaxLength(5)

    def _enable_buttons(self):
        """Set states of the action buttons."""
        # `Stop` is unabled at the beginning.
        self._gui.action_buttons["Stop"].setEnabled(False)
        # `Stop` is unables when being clicked and `Start` is enabled.
        self._gui.action_buttons["Stop"].clicked.connect(
            lambda: self._gui.action_buttons["Stop"].setEnabled(False)
        )
        self._gui.action_buttons["Stop"].clicked.connect(
            lambda: self._gui.action_buttons["Start"].setEnabled(True)
        )

    def _connect_actions(self):
        self._gui.action_buttons["Start"].clicked.connect(self._click_start)
        # `Stop` closes the application window.
        self._gui.action_buttons["Stop"].clicked.connect(self._model.close)
        # `Exit` closes the application windows and GUI.
        self._gui.action_buttons["Exit"].clicked.connect(self._model.close)
        self._gui.action_buttons["Exit"].clicked.connect(self._gui.close)

    def _click_start(self):
        # To be able to do some validations before a real start,
        # put all connections in another method instead of directly
        # connecting them.

        # Check inputs if `Distance Measure` is selected.
        if self._gui.options["Distance Measure"].isChecked():
            if not self._check_inputs_validity():
                return

        # If button `Start` is clicked successfully,
        # unable `Start` and enable `Stop`.
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
        self._model.enable_focus_time(self._gui.options["Focus Time"].isChecked())
        self._model.enable_posture_detect(self._gui.options["Posture Detect"].isChecked())
        if self._gui.options["Distance Measure"].isChecked():
            self._model.enable_distance_measure(
                True,
                face_width=float(self._gui.settings["Face Width"].text()),
                distance=float(self._gui.settings["Distance"].text())
            )
        else:
            self._model.enable_distance_measure(False, 0, 0)
