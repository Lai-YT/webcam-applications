import cv2
import numpy as np


class BrightnessCalculator():
    """Handle processes which require value modulation."""
    def __init__(self):
        super().__init__()

    @staticmethod
    def _get_frame_brightness(frame: np.ndarray) -> int:
        """Returns the percentage of brightness mean."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Value is as known as brightness.
        hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        return int(100 * value.mean() / 255)

    def get_modified_brightness(self, threshold: int, frame: np.ndarray) -> int:
        """Get the brightness percentage of the frame
            and return the modified brightness value.
        """
        # Formula of modifiction
        frame_brightness = self._get_frame_brightness(frame)
        offest = int((frame_brightness - threshold) / 2)
        modified_brightness = threshold + offest

        # The range of the brightness value is (0, 100), 
        # value which is out of range has the same effect as boundary value.
        if modified_brightness > 100:
            modified_brightness = 100
        elif modified_brightness < 0:
            modified_brightness = 0

        return modified_brightness