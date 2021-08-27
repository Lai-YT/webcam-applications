from functools import partial

from PyQt5.QtGui import QDoubleValidator, QIntValidator

from view import ApplicationGui


# Controller handles the states of GUI's components,
# extract the inputs from users and pass them to Model.
class GuiController:
    def __init__(self, model, gui):
        self._model = model
        self._gui = gui

        self._set_valid_input()
        self._enable_buttons()
        self._connect_actions()

    def _set_valid_input(self):
        """Set valid input of the settings."""
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
        # `Restart` is unabled at the beginning.
        self._gui.action_buttons["Restart"].setEnabled(False)
        # Once the application starts, `Restart` becomes enabled and `Start` becomes unabled.
        self._gui.action_buttons["Start"].clicked.connect(
            partial(self._gui.action_buttons["Start"].setEnabled, False)
        )
        self._gui.action_buttons["Start"].clicked.connect(
            partial(self._gui.action_buttons["Restart"].setEnabled, True)
        )

    def _connect_actions(self):
        self._gui.action_buttons["Exit"].clicked.connect(self._model.close)
        self._gui.action_buttons["Exit"].clicked.connect(self._gui.close)
        # Validates the inputs before taking them into execution.
        self._gui.action_buttons["Start"].clicked.connect(self._validate_inputs)
        self._gui.action_buttons["Restart"].clicked.connect(self._validate_inputs)

    def _validate_inputs(self):
        """Check whether the parameters that Distance Detection needs is in the range."""
        has_invalid_input = False
        # When invalid parameter occurs, that parameter line is cleared
        # and the error message shown after the option `Distance Measure`.
        for parameter_line in self._gui.settings.values():
            if not parameter_line.hasAcceptableInput():
                has_invalid_input = True
                parameter_line.clear()
                self._gui.option_msgs["Distance Measure"].setText("error: parameter out of range")

        if not has_invalid_input:
            # Clear the message label to make sure no previous error.
            self._gui.option_msgs["Distance Measure"].clear()
            self._start_capturing()

    def _start_capturing(self):
        self._model.enable_distance_detection(
            self._gui.options["Distance Measure"].isChecked(),
            face_width=float(self._gui.settings["Face Width"].text()),
            distance=float(self._gui.settings["Distance"].text())
        )
        self._model.enable_timer(self._gui.options["Timer"].isChecked())
        self._model.enable_posture_detection(self._gui.options["Posture Detection"].isChecked())
        self._model.start()
