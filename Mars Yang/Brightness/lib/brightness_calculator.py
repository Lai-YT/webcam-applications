import cv2
import numpy as np


class BrightnessCalculator():
    """Handle processes which require value modulation."""
    def __init__(self):
        super().__init__()

    def get_frame_brightness(self, frame: np.ndarray) -> int:
        """Returns the percentage of brightness mean."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # hue, saturation, value
        # Value is as known as brightness.
        h, s, v = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        
        return int(100 * v.mean() / 255)

    def get_modified_brightness(self, slider_brightness: int, frame: np.ndarray) -> int:
        """Get the brightness percentage of the frame
            and return the modified brightness value.
        """
        # Frame brightness = 60, offset = 15; frame brightness = 0, offset = -15.
        frame_brightness = self.get_frame_brightness(frame)
        offest = int((frame_brightness - 30) / 2)
        modified_brightness = slider_brightness + offest

        # The range of the brightness value is (0, 100), 
        # value which is out of the range has the same effect as boundary value.
        if modified_brightness > 100:
            modified_brightness = 100
        elif modified_brightness < 0:
            modified_brightness = 0

        return modified_brightness