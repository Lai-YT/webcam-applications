from PyQt5.QtCore import QObject, pyqtSlot

from lib.brightness_controller import BrightnessController
from lib.main_window import MainGui


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

        # Start a new controller.
        if selected_mode:
            self._brightness_controller = BrightnessController(selected_mode)
            self._process_after_controller_initialized()
        else:
            print("Please choose one of the modes (webcam/color-system).")

    @pyqtSlot()
    def _process_after_controller_initialized(self):
        """
        Disable start button and connect signals 
        after BrightnessController initialized.
        """
        self._gui.buttons["Start"].setEnabled(False)
        self._brightness_controller.enable_start_button.connect(
            lambda: self._gui.buttons["Start"].setEnabled(True)
        )