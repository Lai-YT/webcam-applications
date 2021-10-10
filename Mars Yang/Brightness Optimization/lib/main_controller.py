from PyQt5.QtCore import QObject, pyqtSlot

from lib.brightness_controller import BrightnessController
from lib.component import FailMessageBox
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

    def _get_mode_to_apply(self):
        """Gets the mode user chooses, None if none of the modes are choosed."""
        selected_mode = []
        for mode, radio_button in self._gui.modes.items():
            if radio_button.isChecked():
                selected_mode.append(mode)
        return selected_mode

    def _click_start(self):
        """Confirm the mode and start the process."""
        selected_mode = self._get_mode_to_apply()

        # Start a new controller.
        if len(selected_mode) == 1:
            self._brightness_controller = BrightnessController(selected_mode[0])
        elif len(selected_mode) == 2 :
            self._brightness_controller = BrightnessController("both")
        else:
            FailMessageBox("Please choose one of the modes (webcam/color-system).").exec()
        self._do_process_after_controller_initialized()

    @pyqtSlot()
    def _do_process_after_controller_initialized(self):
        """Disable start button and connect signals after BrightnessController initialized.
        Note that this method should be called after brightness_controller is
        initialized; otherwise AttributeError will be raised.
        """
        self._gui.buttons["Start"].setEnabled(False)
        self._brightness_controller.s_widget_exited.connect(
            lambda: self._gui.buttons["Start"].setEnabled(True)
        )
