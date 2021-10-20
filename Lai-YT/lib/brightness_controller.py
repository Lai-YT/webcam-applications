import cv2
import numpy as np
import screen_brightness_control as sbc

from PyQt5.QtWidgets import QApplication

from lib.brightness_calcuator import BrightnessCalculator

class BrightnessController:

    def __init__(self) -> None:
        self._mode = None
        self._frame = {
            "webcam": None,
            "color-system": None,
        }
        self._threshold = {
            "webcam": None,
            "color-system": None,
        }

    def set_mode(self, mode: str):
        self._mode = mode

    def collect_webcam_frame(self, frame):
        self._frame["webcam"] = frame

    def collect_screenshot(self):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(QApplication.desktop().winId())

        self._frame["color-system"] = self._qpixmap_to_ndarray(screenshot)

    @staticmethod
    def _qpixmap_to_ndarray(image: "QPixmap") -> "NDArray[(Any, Any, 3), UInt8]":
        qimage = image.toImage()

        width = qimage.width()
        height = qimage.height()

        byte_str = qimage.constBits().asstring(height * width * 4)
        ndarray = np.frombuffer(byte_str, np.uint8).reshape((height, width, 4))

        return ndarray

    def get_optimized_brightness(self, base_value: int):
        return BrightnessCalculator.calculate_proper_screen_brightness(
            self._mode, base_value, self._frame)

    def _set_brightness(self, brightness: int):
        sbc.set_brightness(brightness, method="wmi")
