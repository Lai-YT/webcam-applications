import cv2
import numpy as np


class BrightnessCalculator:
    """Handle processes which require value modulation."""

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

    @staticmethod
    def calculate_proper_screen_brightness(mode: str, threshold: int, base_value: int, frame: np.ndarray) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode ("webcam" | "color-system"): Mode affects algorithm used in calculation
            threshold (int): The brightness of the initial frame, affecting the offset value.
            base_value (int): The base value of brightness (The value before checking the checkbox).
            frame (NDArray[(Any, Any, 3), UInt8)
        """
        if mode == "webcam":
            frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frame)
            offest: int = (frame_brightness - threshold) // 2
            suggested_brightness: int = base_value + offest

            # The range of the brightness value is (0, 100),
            # value which is out of range has the same effect as boundary value.
            if suggested_brightness > 100:
                suggested_brightness = 100
            elif suggested_brightness < 0:
                suggested_brightness = 0
        else: # mode == "color-system"
            pass
            
        return suggested_brightness
