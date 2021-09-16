import cv2

import screen_brightness_control as sbc
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from lib.brightness_calculator import BrightnessCalculator
from lib.brightness_window import BrightnessGui


method = "wmi"
class BrightnessController(QObject):
    s_exit = pyqtSignal()

    def __init__(self, gui: BrightnessGui):
        super().__init__()
    
        self._gui = gui
        self._calc = BrightnessCalculator()
        self.set_brightness(20)
        self.connect_signals()

    def connect_signals(self):
        """Connect the siganls among widgets."""
        self._gui.buttons["Start"].clicked.connect(self.click_start)
        self._gui.buttons["Exit"].clicked.connect(self.click_exit)
        self._gui.slider.valueChanged.connect(
            lambda: self.set_brightness(self._gui.slider.value()))
        """Connect the exit signal."""
        self.s_exit.connect(self._gui.close)

    def set_brightness(self, brightness: int):
        """Adjust the brightness of the screen by sliding the slider."""
        self._gui.label.setText(f'Brightness: {brightness}')
        sbc.set_brightness(brightness, method=method)

    @pyqtSlot()
    def capture_image(self):
        """Capture images and adjust the brightness instantly."""
        cam = cv2.VideoCapture(0)

        # If exit flag is True, jump out the loop.
        while not self._gui.exit_flag:
            _, frame = cam.read()
            frame = cv2.flip(frame, flipCode=1) # horizontally flip
            
            # If "Lock" is checked, skip the adjustion part.
            if not self._gui.lock.isChecked():
                brightness = self._calc.get_modified_brightness(frame)
                self.set_brightness(brightness)

            cv2.imshow('Video Capture', frame)
            cv2.waitKey(25)

        # Close the webcam and emit the exit signal.
        self.set_brightness(20)
        cam.release()
        self.s_exit.emit()
        cv2.destroyAllWindows()

    def click_start(self):
        """Do things after start button is clicked."""
        self._gui.slider.hide()
        self._gui.lock.show()
        self._gui.buttons["Exit"].setEnabled(True)
        self._gui.buttons["Start"].setEnabled(False)
        self.capture_image()

    def click_exit(self):
        """Set exit flag to True."""
        self._gui.exit_flag = True