from typing import Dict, Optional

import cv2
import numpy as np
import screen_brightness_control as sbc
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QApplication

from lib.brightness_calcuator import BrightnessCalculator, BrightnessMode
from lib.image_convert import qpixmap_to_ndarray
from lib.image_type import ColorImage


class BrightnessController(QObject):
    """BrightnessController adjusts the brightness of screen depending on the mode
    you set.

    Signals:
        s_brightness_refreshed:
            Emits everytime a new brightness is set.
            It sends the new brightness value.
    """

    s_brightness_refreshed = pyqtSignal(int)

    def __init__(self,
                 mode: Optional[BrightnessMode] = None,
                 base_value: Optional[int] = None,
                 frames: Optional[Dict[BrightnessMode, ColorImage]] = None) -> None:
        """
        All arguments are with default None. They can be set later with
        their corresponding setters.

        Arguments:
            mode: Mode that the brightness adjustment depends on.
            base_value:
                The user's screen brightness preference. Brightness is adjusted
                up and down with respect to it.
            frames: Used to compare brightness with the base value to can get the new brightness.
        """
        super().__init__()

        if mode is not None:
            self._mode: BrightnessMode = mode
        if base_value is not None:
            self._base_value: int = base_value
        self._frames: Dict[BrightnessMode, ColorImage] = {}
        if frames is not None:
            self._frames = frames

    def set_mode(self, mode: BrightnessMode) -> None:
        """
        Arguments:
            mode: Mode that the brightness adjustment depends on.
        """
        self._mode = mode

    def set_webcam_frame(self, frame: ColorImage) -> None:
        """
        Arguments:
            frame:
                The image used to compare brightness with in WEBCAM (BOTH) mode.
        """
        self._frames[BrightnessMode.WEBCAM] = frame

    def set_base_value(self, base_value: int) -> None:
        """
        Arguments:
            base_value:
                The user's screen brightness preference. Brightness is adjusted
                up and down with respect to it.
        """
        self._base_value = base_value

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

        Signal s_brightness_refreshed is emitted with the new brightness value.

        Notice that this method does nothing is any of the above attributes
        aren't set.
        """
        if not hasattr(self, "_mode") or not hasattr(self, "_base_value") or not self._frames:
            return

        new_brightness = BrightnessCalculator.calculate_proper_screen_brightness(self._mode, self._base_value, self._frames)
        sbc.set_brightness(new_brightness, method="wmi")
        self.s_brightness_refreshed.emit(new_brightness)