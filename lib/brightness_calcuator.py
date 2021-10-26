from enum import Enum, auto
from typing import Dict

import cv2

from lib.image_type import ColorImage


class BrightnessMode(Enum):
    """The modes that BrightnessCalculator uses."""
    WEBCAM = auto()
    COLOR_SYSTEM = auto()
    BOTH = auto()
    MANUAL = auto()


class BrightnessCalculator:
    """Handle processes which require value modulation."""

    @staticmethod
    def calculate_proper_screen_brightness(
            mode: BrightnessMode,
            base_value: int,
            frames: Dict[BrightnessMode, ColorImage]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode: Mode affects algorithm used in calculation.
            base_value: The base value of brightness (The value before checking the checkbox).
            frames:
                Image of the corresponding brightness mode. If mode is BOTH, there should be two frames.
        """
        # Get the brightness precentage of the frame(s).
        if mode is BrightnessMode.WEBCAM or mode is BrightnessMode.BOTH:
            webcam_frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.WEBCAM])
        if mode is BrightnessMode.COLOR_SYSTEM or mode is BrightnessMode.BOTH:
            color_system_frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.COLOR_SYSTEM])

        # Higher the brightness if the environment is bright to keep the screen clear.
        if mode is BrightnessMode.WEBCAM:
            offset: int = (webcam_frame_brightness - base_value) // 2
        # Lower the brightness if the background of screen is light colored.
        elif mode is BrightnessMode.COLOR_SYSTEM:
            offset = -(color_system_frame_brightness - base_value) // 2
        # Algorithm of BOTH is not simply an additon of the above.
        # WEBCAM takes the lead and has COLOR_SYSTEM with a smaller factor.
        elif mode is BrightnessMode.BOTH:
            offset = ((webcam_frame_brightness - base_value) // 2
                      - (color_system_frame_brightness - base_value) // 4)
        # The range of the screen brightness value is [0, 100].
        suggested_brightness: int = BrightnessCalculator._clamp(base_value + offset, 0, 100)

        return suggested_brightness

    @staticmethod
    def get_brightness_percentage(frame: ColorImage) -> int:
        """Returns the mean of brightness of the frame.

        Arguments:
            frame: The image to perform brightness calculation on.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        return int(100 * value.mean() / 255)

    @staticmethod
    def _clamp(value: int, v_min: int, v_max: int) -> int:
        """Clamps the value into the range [v_min, v_max].

        e.g., _clamp(50, 20, 40) returns 40.
        v_min should be less or equal to v_max. (v_min <= v_max)
        """
        if not v_min < v_max:
            raise ValueError("v_min is the lower bound, which should be smaller than v_max")

        if value > v_max:
            value = v_max
        elif value < v_min:
            value = v_min
        return value
