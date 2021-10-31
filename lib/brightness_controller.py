from typing import Dict, Optional

import screen_brightness_control as sbc
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from lib.brightness_calcuator import BrightnessCalculator, BrightnessMode
from lib.image_convert import qpixmap_to_ndarray
from lib.image_type import ColorImage


class BrightnessController(QObject):
    """BrightnessController adjusts the brightness of screen depending on the
    mode you set.

    Signals:
        s_brightness_refreshed:
            Emits everytime optimize_brightness is called.
            It sends the new brightness value if a new brightness is set;
            otherwise it sends the current brightness value.
    """

    s_brightness_refreshed = pyqtSignal(int)

    def __init__(self,
                 mode: BrightnessMode = BrightnessMode.MANUAL,
                 base_value: Optional[int] = None,
                 frames: Optional[Dict[BrightnessMode, ColorImage]] = None) -> None:
        """
        All arguments can be set later with their corresponding setters.

        Arguments:
            mode: Mode that the brightness adjustment depends on.
            base_value:
                The user's screen brightness preference. Brightness is adjusted
                up and down with respect to it.
            frames: Used to compare brightness with the base value to can get the new brightness.
        """
        super().__init__()

        self._mode: BrightnessMode = mode
        if base_value is not None:
            self._base_value: int = base_value
        self._frames: Dict[BrightnessMode, ColorImage] = {}
        if frames is not None:
            self._frames = frames
        self._brightness_calculator = BrightnessCalculator()

    def set_mode(self, mode: BrightnessMode) -> None:
        """
        Arguments:
            mode: Mode that the brightness adjustment depends on.
        """
        self._mode = mode

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
        screen = QApplication.primaryScreen()
        screenshot: QPixmap = screen.grabWindow(QApplication.desktop().winId())

        self._frames[BrightnessMode.COLOR_SYSTEM] = qpixmap_to_ndarray(screenshot)

    def optimize_brightness(self) -> None:
        """Sets brightness of screen to a suggested brightness with respect to
        mode, the base value and frames.

        Notice that this method doesn't get and set new brightness value if any
        of the above attributes aren't set.

        Emits:
            s_brightness_refreshed:
                If all attributes required are set, it sends the new brightness
                value; otherwise it sends the current brightness value.
        """
        if (self._mode is BrightnessMode.MANUAL
                or not hasattr(self, "_base_value")
                or not self._frames):
            self._brightness_calculator.clear()
            sbc.set_brightness(self._base_value, method="wmi")
            self.s_brightness_refreshed.emit(self._base_value)
        else:
            new_brightness: int = (
                self._brightness_calculator.calculate_proper_screen_brightness(
                    self._mode, self._base_value, self._frames)
            )
            sbc.set_brightness(new_brightness, method="wmi")
            self.s_brightness_refreshed.emit(new_brightness)
