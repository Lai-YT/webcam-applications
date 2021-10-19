import cv2
import numpy as np
from typing import Dict


class BrightnessCalculator:
    """Handle processes which require value modulation."""

    @staticmethod
    def calculate_proper_screen_brightness(mode: str, base_value: int, frame: Dict[str, np.ndarray]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode ("webcam" | "color-system"): Mode affects algorithm used in calculation
            base_value (int): The base value of brightness (The value before checking the checkbox).
            frame (NDArray[(Any, Any, 3), UInt8)
        """
        if frame["webcam"] is not None:
            webcam_frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frame["webcam"])
        if frame["color-system"] is not None:
            color_system_frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frame["color-system"])
        
        if mode == "webcam":
            offset: int = (webcam_frame_brightness - base_value) // 2
        elif mode == "color-system":
            offset: int = -(color_system_frame_brightness - base_value) // 2
        elif mode == "both":
            offset = (webcam_frame_brightness - base_value) // 2
            offset = offset + (color_system_frame_brightness - base_value) // 4

        suggested_brightness: int = base_value + offset

        # The range of the brightness value is (0, 100),
        # value which is out of range has the same effect as boundary value.
        if suggested_brightness > 100:
            suggested_brightness = 100
        elif suggested_brightness < 0:
            suggested_brightness = 0

        return suggested_brightness

    @staticmethod
    def get_brightness_percentage(frame: np.ndarray) -> int:
        """Returns the mean of brightness of the frame.

        Arguments:
            frame (NDArray[(Any, Any, 3), UInt8])
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        return int(100 * value.mean() / 255)