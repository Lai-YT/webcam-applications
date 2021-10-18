import cv2
import screen_brightness_control as sbc

from PyQt5.QtWidgets import QApplication

from lib.brightness_calcuator import BrightnessCalculator

class BrightnessController:

    def __init__(self, mode) -> None:
        self._mode = mode
        self._frame = {
            "webcam": None,
            "color-system": None,
        }
        self._threshold = {
            "webcam": None,
            "color-system": None,
        }

    def collect_webcam_frame(self, frame):
        self._frame["webcam"] = frame

    def collect_screenshot(self):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(QApplication.desktop().winId())

        self._frame["color-system"] = screenshot

    def optimize_brightness(self, base_value: int):
        brightness = BrightnessCalculator.calculate_proper_screen_brightness(
            self._mode, base_value, self._frame)
        
        self._set_brightness(brightness)

    def _set_brightness(self, brightness: int):
        sbc.set_brightness(brightness, method="wmi")
