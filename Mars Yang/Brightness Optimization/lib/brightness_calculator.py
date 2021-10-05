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
        if mode == "webcam":
            frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frame)
            offest: int = (frame_brightness - threshold) // 2
            suggested_brightness: int = base_value + offest
        else: # mode == "color-system"
            # list of light colors
            light_colors = {
                "white", "light red", "orange", "yellow", "green", "cyan"
            }
    
            dominant_color = BrightnessCalculator.get_dominant_color(frame)
            if dominant_color in light_colors:
                offset = -20
            else:
                offset = 10
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

    @staticmethod
    def get_dominant_color(frame):
        """Return the dominant color of the frame."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        max_area = -1  # Since area won't be less than 0, -1 indicates the absolute minimum.
        dominant_color = None
        for color, bounds in COLOR_DICT.items():
            mask = cv2.inRange(hsv, *bounds)  # values in bound => 255, out of => 0
            binary = cv2.dilate(mask, None, iterations=2)

            # Get the contours that circles the colored areas.
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