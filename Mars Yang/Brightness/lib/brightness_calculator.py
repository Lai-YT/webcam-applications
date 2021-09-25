import cv2
import numpy as np


class BrightnessCalculator:
    """Handle processes which require value modulation."""

    def get_frame_brightness(frame: np.ndarray) -> int:
        """Returns the percentage of brightness mean."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        # Value is as known as brightness.
        hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        return int(100 * value.mean() / 255)
    
    @staticmethod
    def get_modified_brightness(threshold: int, base_value: int, frame: np.ndarray) -> int:
        """Get the brightness percentage of the frame
            and return the modified brightness value.
    
        Arguments:
            threshold: The brightness of the initial frame, affecting the offset value.
            base_value: The base value of brightness (The value before checking the checkbox). 
        """

        frame_brightness = BrightnessCalculator.get_frame_brightness(frame)
        offest = int((frame_brightness - threshold) / 2)
        modified_brightness = base_value + offest

        # The range of the brightness value is (0, 100), 
        # value which is out of range has the same effect as boundary value.
        if modified_brightness > 100:
            modified_brightness = 100
        elif modified_brightness < 0:
            modified_brightness = 0

        return modified_brightness