from typing import Dict

import screen_brightness_control as sbc
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from brightness.calcuator import BrightnessCalculator, BrightnessMode
from util.image_convert import qpixmap_to_ndarray
from util.image_type import ColorImage


class BrightnessController:
    """Store arguments and controls the optimizing method."""
    def __init__(self, base_value: int, mode: BrightnessMode) -> None:
        """
        All arguments can be set later with their corresponding setters.

        Arguments:
            base_value:
                The user's screen brightness preference.
                Brightness will be fine-tuned based on the base value.
            mode: The attribute affecting the algorithm of optimizing method.
        """
        super().__init__()

        # frame dict is empty if no frame passed
        self._frames: Dict[BrightnessMode, ColorImage] = {}
        self._brightness_calculator = BrightnessCalculator(mode, base_value)

    def set_mode(self, new_mode: BrightnessMode) -> None:
        """
        Arguments:
            new_mode: Mode that the brightness adjustment depends on.
        """
        self._brightness_calculator.set_mode(new_mode)

    def get_mode(self) -> BrightnessMode:
        """Returns the brightness mode used by the controller."""
        return self._brightness_calculator.get_mode()

    def update_base_value(self, new_base_value: int) -> None:
        """
        Arguments:
            new_base_value: The user's screen brightness preference.
        """
        self._brightness_calculator.update_base_value(new_base_value)

    def update_webcam_frame(self, frame: ColorImage) -> None:
        """
        Arguments:
            frame:
                The image used to weight brightness value in optimizing method
                with WEBCAM (BOTH) mode.
        """
        self._frames[BrightnessMode.WEBCAM] = frame

    def refresh_color_system_screenshot(self) -> None:
        """Takes a screenshot of the current screen and sets it as the frame of
        COLOR_SYSTEM mode.
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
        optimized_brightness: int = (
            self._brightness_calculator.calculate_proper_screen_brightness(
                self._frames
            )
        )
        sbc.set_brightness(optimized_brightness, method="wmi")
        return optimized_brightness
