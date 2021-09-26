import cv2
from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot
import screen_brightness_control as sbc

from lib.brightness_calculator import BrightnessCalculator
from lib.brightness_window import BrightnessGui


method = "wmi"
class BrightnessController(QObject):
    # Emits when the `Exit` button is clicked.
    s_exit = pyqtSignal()

    def __init__(self, gui: BrightnessGui):
        super().__init__()

        self._gui = gui
        # Since there are multiple fuctions that need to access camera,
        # make it an attribute instead of opening in a certain method.
        self.cam = cv2.VideoCapture(0)

        self._connect_signals()
        # Init the slider and label status to be as same as the user's screen brightness.
        self._set_brightness(sbc.get_brightness(method=method), set_slider=True)

        self._capture_image()

    def _connect_signals(self):
        # Connect the siganls among widgets.
        self._gui.buttons["Exit"].clicked.connect(self._click_exit)
        # The base brightness values update each time the user check the box.
        # And the screen brightness is the last automatically adjusted valeu after
        # the user uncheck the box.
        self._gui.checkbox.stateChanged.connect(
            lambda state: \
            self._update_base_brightness_values() if state == Qt.Checked \
            else self._set_brightness(sbc.get_brightness(method=method), set_slider=True))
        # Label and screen should be set when the user adjust the slider.
        self._gui.slider.valueChanged.connect(
            lambda: self._set_brightness(self._gui.slider.value(), set_slider=False))
        # Connect the exit signal.
        self.s_exit.connect(self._gui.close)

    def _set_brightness(self, brightness: int, set_slider: bool):
        """Adjust the brightness of the screen manually or automatically.

        Arguments:
            brightness (int): The brightness value to set to the screen
            set_slider (bool): The value of slider will also be set is True
        """
        if set_slider:
            self._gui.slider.setValue(brightness)
        self._gui.label.setText(f"Brightness: {brightness}")
        sbc.set_brightness(brightness, method=method)

    @pyqtSlot()
    def _update_base_brightness_values(self):
        """Updates the base environment and screen brightness value.
        They will be passed to the BrightnessCalculator to calculate modified brightness.
        """
        _, environment_image = self.cam.read()
        # threshold is the brightness value of the environment.
        self._threshold = BrightnessCalculator.get_brightness_percentage(environment_image)
        # base value is the brightness value of the screen under such environment,
        # which is the current slider value.
        self._base_value = self._gui.slider.value()

    def _capture_image(self):
        """Capture images and adjust the brightness instantly."""
        self._f_exit = False

        while not self._f_exit:
            _, frame = self.cam.read()
            frame = cv2.flip(frame, flipCode=1) # horizontally flip

            # If "Brightness Optimization" is checked, adjust the brightness automatically;
            # otherwise, users can adjust by themselves.
            if self._gui.checkbox.isChecked():
                self._gui.slider.hide()
                brightness = BrightnessCalculator.calculate_proper_screen_brightness(self._threshold, self._base_value, frame)
                # The value of the slider is kept unchanged, only the label and
                # the brightness of screen is adjusted.
                # This is because the slider is only used to change the base value,
                # which should be adjusted by the user.
                self._set_brightness(brightness, set_slider=False)
            else:
                self._gui.slider.show()
            cv2.waitKey(25)

        # Close the webcam and emit the exit signal.
        self.cam.release()
        cv2.destroyAllWindows()
        self.s_exit.emit()
        # TODO:
        # The event loop doesn't end after the top-level window is closed.
        # Using sys.exit is a poor workaround.
        # import sys
        # sys.exit(0)

    @pyqtSlot()
    def _click_exit(self):
        """Set exit flag to True."""
        self._f_exit = True
