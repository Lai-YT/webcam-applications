from typing import Dict

import screen_brightness_control as sbc
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from brightness.calcuator import BrightnessCalculator, BrightnessMode
from util.image_convert import qpixmap_to_ndarray
from util.image_type import ColorImage


class BrightnessController:
    """BrightnessController adjusts the brightness of screen depending on the
    mode you set.
    """
    def __init__(self, base_value: int, mode: BrightnessMode) -> None:
        """
        All arguments can be set later with their corresponding setters.

        Arguments:
            base_value:
                The user's screen brightness preference.
                Brightness is adjusted up and down with respect to it.
            mode: Mode that the brightness adjustment depends on.
            frames:
                Used to compare brightness with the base value to can get
                the new brightness.
        """
        super().__init__()

        self._mode: BrightnessMode = mode
        self._base_value: int = base_value
        # frame dict is empty if no frame passed
        self._frames: Dict[BrightnessMode, ColorImage] = {}
        self._brightness_calculator = BrightnessCalculator()

    def set_mode(self, mode: BrightnessMode) -> None:
        """
        Arguments:
            mode: Mode that the brightness adjustment depends on.
        """
        self._mode = mode

    def get_mode(self) -> BrightnessMode:
        """Returns the brightness mode used by the controller."""
        return self._mode

    def set_base_value(self, base_value: int) -> None:
        """
        Arguments:
            base_value:
                The user's screen brightness preference. Brightness is adjusted
                up and down with respect to it.
        """
        self._base_value = base_value

    def set_webcam_frame(self, frame: ColorImage) -> None:
        """
        Arguments:
            frame:
                The image used to compare brightness with in WEBCAM (BOTH) mode.
        """
        self._frames[BrightnessMode.WEBCAM] = frame

    def refresh_color_system_screenshot(self) -> None:
        """Takes a screenshot of the current screen and sets it as the frame of
        color system.
        """
        screenshot: QPixmap = (
            QApplication.primaryScreen().grabWindow(QApplication.desktop().winId()))

        self._frames[BrightnessMode.COLOR_SYSTEM] = qpixmap_to_ndarray(screenshot)

    def optimize_brightness(self) -> int:
        """Sets brightness of screen to a suggested brightness with respect to
        mode, the base value and frames.

        Returns:
            The brightness value after optimization.
        """
        value: int
        if self._mode is BrightnessMode.MANUAL or not self._frames:
            # The latest use of the brightness calculator is finished,
            # so it is reset to clean all weighted value of the history.
            self._brightness_calculator.reset()
            # No new value, the current brightness value is set.
            value = sbc.get_brightness(method="wmi")
        else:
            new_brightness: int = (
                self._brightness_calculator.calculate_proper_screen_brightness(
                    self._mode, self._base_value, self._frames)
            )
            value = new_brightness
        sbc.set_brightness(value, method="wmi")
        return value
