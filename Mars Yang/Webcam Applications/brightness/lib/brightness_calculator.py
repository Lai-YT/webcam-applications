import cv2
import numpy as np

from lib.color_lib import COLOR_DICT


class BrightnessCalculator:
    """Handle processes which require value modulation."""

    @staticmethod
    def calculate_proper_screen_brightness(mode: str, threshold: int, base_value: int, frame: np.ndarray) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode ("webcam" | "color-system"): Mode affects algorithm used in calculation
            threshold (int): The brightness of the initial frame, affecting the offset value.
            base_value (int): The base value of brightness (The value before checking the checkbox).
            frame (NDArray[(Any, Any, 3), UInt8)
        """
        frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frame)

        if mode == "webcam":
            offset: int = (frame_brightness - threshold) // 2
        elif mode == "color-system":
            offset: int = -(frame_brightness - threshold) // 2

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

    # reference: https://github.com/sunny-fang/SunnyFang-Collection/blob/cea68c9df1b07688424a6ba71167c9aac248cb9e/Graduate%20School/Python%20related/Main%20color%20analysis/%E4%B8%BB%E8%89%B2%E7%B3%BB%E5%88%86%E6%9E%90.py
    @staticmethod
    def get_dominant_color(frame):
        """Returns the dominant color of the image, which occupies the most area."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        max_area = -1  # Since area won't be less than 0, -1 indicates the absolute minimum.
        dominant_color = None
        for color, bounds in COLOR_DICT.items():
            # values in bound => 255, out of => 0
            mask = cv2.inRange(hsv, *bounds)
            # Dilate to have the color areas connect together.
            binary = cv2.dilate(mask, None, iterations=2)
            # Get the contours that circles the color area.
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # Calculate the total area of this color.
            # And store as the current dominant color if this color has the current max area.
            area = 0
            for cnt in contours:
                area += cv2.contourArea(cnt)
            if area > max_area:
                max_area = area
                dominant_color = color

        return dominant_color