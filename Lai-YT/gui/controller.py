from functools import partial

from PyQt5.QtGui import QDoubleValidator, QIntValidator

from view import ApplicationGui


class GuiController:
    def __init__(self, gui):
        self._gui = gui
        self._set_valid_input()
        self._enable_buttons()
        self._connect_actions()

    def _set_valid_input(self):
        """Set valid input of the settings."""
        for line in self._gui.settings.values():
            # The user is still able to key in 00000~99999,
            # `intermediate` inputs will be found at the button event stage
            # and error message will shown.
            line.setValidator(QDoubleValidator(0.99, 99.99, 2))  # bottom, top, decimals
            line.setMaxLength(5)

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
        self._gui.action_buttons["Exit"].clicked.connect(self._gui.close)
