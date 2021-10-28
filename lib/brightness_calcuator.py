from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple

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

    def __init__(self) -> None:
        # Init previous weighted value.
        self._pre_weighted_value: Optional[float] = None

    def calculate_proper_screen_brightness(
            self,
            mode: BrightnessMode,
            base_value: int,
            frames: Dict[BrightnessMode, ColorImage]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode: Mode affects algorithm used in calculation.
            base_value: The base value of brightness (The value before checking the checkbox).
            frames:
                Image of the corresponding brightness mode.
                If mode is BOTH, there should have two frames.
        """
        # Prepare the brightness precentage of the frame(s) that will be used
        # under the corresponding mode.
        if mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            webcam_frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.WEBCAM])
        if mode in (BrightnessMode.COLOR_SYSTEM, BrightnessMode.BOTH):
            screenshot_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.COLOR_SYSTEM])
        if mode is BrightnessMode.BOTH:
            # webcam frame takes the lead
            weighted_frame_brightness: float = _weighted_sum(
                (webcam_frame_brightness, 0.6),
                (100-screenshot_brightness, 0.4)
            )

        # All remain weights are on self._pre_weighted_value.
        weight_of_modes: Dict[BrightnessMode, Tuple[str, float]] = {
            BrightnessMode.WEBCAM: ("webcam_frame_brightness", 0.4),
            BrightnessMode.COLOR_SYSTEM: ("screenshot_brightness", 0.4),
            BrightnessMode.BOTH: ("weighted_frame_brightness", 0.4),
        }

        # locals() returns the local_vars with type Dict[str, Any]
        frame_brightness: float = locals()[weight_of_modes[mode][0]]
        brightness_weight: float = weight_of_modes[mode][1]
        if self._pre_weighted_value is None:
            # _pre_weighted_value takes no more weight
            new_weighted_value: float = frame_brightness * 1
        else:
            new_weighted_value = _weighted_sum(
                (frame_brightness, brightness_weight),
                (self._pre_weighted_value, 1-brightness_weight)
            )
        # Update previous value.
        self._pre_weighted_value = new_weighted_value

        # base value (from slider) takes the lead of optimization and has weighted
        # brightness with a smaller weight.
        # Higher the brightness if the environment is bright to keep the screen clear and
        # lower the brightness if the background of screen is light colored.
        if mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            suggested_brightness: float = _weighted_sum((base_value, 0.75), (new_weighted_value, 0.25))
        elif mode is BrightnessMode.COLOR_SYSTEM:
            suggested_brightness = _weighted_sum((base_value, 0.75), (100-new_weighted_value, 0.25))

        return int(suggested_brightness)

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


# outer utilities

def _weighted_sum(*number_and_weights: Tuple[float, float]) -> float:
    """Returns the weighted sum of each (number, weight) pair."""
    weighted_sum: float = 0
    for num, weight in number_and_weights:
        weighted_sum += num * weight
    return weighted_sum
