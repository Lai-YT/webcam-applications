from lib.brightness_controller import BrightnessController
from lib.main_window import MainGui
from PyQt5.QtCore import QObject


method = "wmi"
class GuiController(QObject):

    def __init__(self, gui: MainGui):
        super().__init__()

        self._gui = gui

        self._connect_signals()


    def _connect_signals(self):
        # Connect the siganls among widgets.
        self._gui.buttons["Start"].clicked.connect(self._click_start)
        self._gui.buttons["Exit"].clicked.connect(self._gui.close)

    def _check_which_mode_to_apply(self):
        """Check which mode user chooses."""
        for mode, radio_button in self._gui.modes.items():
            if radio_button.isChecked():
                return mode

    def _click_start(self):
        """Confirm the mode and start the process."""
        selected_mode = self._check_which_mode_to_apply()

        if selected_mode:
            self.brightness_controller = BrightnessController(selected_mode)
        else:
            print("Please choose one of the modes (webcam/color-system).")    