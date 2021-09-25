import cv2

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
import screen_brightness_control as sbc

from lib.brightness_calculator import BrightnessCalculator
from lib.brightness_window import BrightnessGui


method = "wmi"
class BrightnessController(QObject):
    s_exit = pyqtSignal()

    def __init__(self, gui: BrightnessGui):
        super().__init__()
    
        self._gui = gui
        self._calc = BrightnessCalculator()
        self._brightness = 30
        self._exit_flag = False

        self._connect_signals()
        self._set_brightness(self._brightness)
        self._capture_image()

    def _connect_signals(self):
        """Connect the siganls among widgets."""
        self._gui.buttons["Exit"].clicked.connect(self._click_exit)
        self._gui.slider.valueChanged.connect(
            lambda: self._set_brightness(self._gui.slider.value()))
        """Connect the exit signal."""
        self.s_exit.connect(self._gui.close)

    def _set_brightness(self, brightness: int):
        """Adjust the brightness of the screen manually or automatically."""
        self._gui.slider.setValue(brightness)
        self._gui.label.setText(f'Brightness: {brightness}')
        sbc.set_brightness(brightness, method=method)

    @pyqtSlot()
    def _capture_image(self):
        """Capture images and adjust the brightness instantly."""
        cam = cv2.VideoCapture(0)

        # If exit flag is True, jump out the loop.
        while not self._exit_flag:
            _, frame = cam.read()
            frame = cv2.flip(frame, flipCode=1) # horizontally flip

            # If "Brightness Optimization" is checked, adjust the brightness automatically;
            # otherwise, users can adjust by themselves.
            if self._gui.checkbox.isChecked():
                self._gui.slider.hide()
                self._brightness = self._calc.get_modified_brightness(self._gui.slider.value(), frame)
                self._set_brightness(self._brightness)
            else:
                self._gui.slider.show()

            cv2.imshow('Video Capture', frame)
            cv2.waitKey(25)

        # Close the webcam and emit the exit signal.
        cam.release()
        cv2.destroyAllWindows()
        self.s_exit.emit()

    def _click_exit(self):
        """Set exit flag to True."""
        self._exit_flag = True