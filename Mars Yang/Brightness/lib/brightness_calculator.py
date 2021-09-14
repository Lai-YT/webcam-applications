import cv2
import numpy as np


class BrightnessCalculator():
    """Handle processes which require value modulation."""
    def __init__(self):
        super().__init__()

    def get_brightness_percentage(self, frame: np.ndarray) -> int:
        """Returns the percentage of brightness mean."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # hue, saturation, value
        # Value is as known as brightness.
        h, s, v = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
            
        return int(100 * v.mean() / 255)

    def get_modified_brightness(self, frame: np.ndarray) -> int:
        """Get the brightness percentage of the frame
            and return the modified brightness value.
        """
        brightness_percentage = self.get_brightness_percentage(frame)

        # brightness percentage >= 50%
        brightness = int(0.8 * brightness_percentage)
        # 30% < brightness percentage < 50%
        if brightness_percentage < 50:
                brightness = int(2 * (brightness_percentage - 30))
        # brightness percentage < 30%
        brightness = 0 if brightness < 0 else brightness
            
        return brightness