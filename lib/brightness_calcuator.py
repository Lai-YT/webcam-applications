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
    def calculate_proper_screen_brightness(mode: BrightnessMode, base_value: int, frames: Dict[BrightnessMode, ColorImage]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode: Mode affects algorithm used in calculation.
            base_value: The base value of brightness (The value before checking the checkbox).
            frames:
                Image of the corresponding brightness mode. If mode is BOTH, there should be two frames.
        """
        # Init previous weighted value.
        pre_weighted_value = 0

        # Get the brightness precentage of the frame(s).
        if mode is BrightnessMode.WEBCAM or mode is BrightnessMode.BOTH:
            webcam_frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.WEBCAM])
        if mode is BrightnessMode.COLOR_SYSTEM or mode is BrightnessMode.BOTH:
            screenshot_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.COLOR_SYSTEM])

        # Weight the frame brightness with pre-weighted value to get new weighted value.
        if mode is BrightnessMode.WEBCAM:
            new_weighted_value = (
                webcam_frame_brightness if pre_weighted_value == 0 else
                webcam_frame_brightness * 0.4 + pre_weighted_value * 0.6
            )
        elif mode is BrightnessMode.COLOR_SYSTEM:
            new_weighted_value = (
                screenshot_brightness if pre_weighted_value == 0 else
                screenshot_brightness * 0.4 + pre_weighted_value * 0.6
            )
        # Algorithm of BOTH
        # First, get the weighted frame brightness by weighting brightness of two frames,
        # then weight the weighted frame brightness with pre-weighted value. 
        elif mode is BrightnessMode.BOTH:
            # WEBCAM frame takes the lead and has COLOR_SYSTEM frame with a smaller factor.
            weighted_frame_brightness = webcam_frame_brightness * 0.6 + (100 - screenshot_brightness) * 0.4
            new_weighted_value = (
                weighted_frame_brightness if pre_weighted_value == 0 else
                weighted_frame_brightness * 0.4 + pre_weighted_value * 0.6
            )
        # Set new weighted value to be previous.
        pre_weighted_value = new_weighted_value
        # Slider value takes the lead of optimization and has weighted brightness with a smaller factor.
        # Higher the brightness if the environment is bright to keep the screen clear and
        # lower the brightness if the background of screen is light colored.
        if mode is BrightnessMode.WEBCAM or BrightnessMode.BOTH:
            suggested_brightness: int = base_value * 0.75 + new_weighted_value * 0.25
        elif mode is BrightnessMode.COLOR_SYSTEM:
            suggested_brightness: int = base_value * 0.75 + (100 - new_weighted_value) * 0.25

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
