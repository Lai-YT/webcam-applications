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
        self._base_value: Optional[int] = None
        self._brightness_value: Optional[float] = None

    def calculate_proper_screen_brightness(
            self,
            mode: BrightnessMode,
            current_base_value: int,
            frames: Dict[BrightnessMode, ColorImage]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode: Mode affects algorithm used in calculation.
            base_value: The base value of brightness (The value before checking the checkbox).
            frames:
                Image of the corresponding brightness mode.
                If mode is BOTH, there should have two frames.
        """
        # Init variables of calculator
        if self._base_value == None:
            self._base_value = current_base_value
        if self._brightness_value == None:
            self._brightness_value = current_base_value
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
            # Set _pre_weighted_value as new_weighted_value to avoid NoneType Error.
            self._pre_weighted_value = new_weighted_value
        else:
            new_weighted_value = _weighted_sum(
                (frame_brightness, brightness_weight),
                (self._pre_weighted_value, 1-brightness_weight)
            )
        # Both value differences affect the brightness value.
        base_value_difference = current_base_value - self._base_value
        weighted_value_difference = int(new_weighted_value - self._pre_weighted_value)

        # Add value difference effect on current brightness value and store the value.
        # Higher the brightness if the environment is bright to keep the screen clear and
        # lower the brightness if the background of screen is light colored.
        if mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            self._brightness_value += base_value_difference + weighted_value_difference * 0.25
        elif mode is BrightnessMode.COLOR_SYSTEM:
            self._brightness_value += base_value_difference - weighted_value_difference * 0.25

        # Clamp brightness value
        self._brightness_value = clamp(self._brightness_value, 0, 100)
        # Update previous value.
        self._base_value = current_base_value
        self._pre_weighted_value = new_weighted_value

        return int(self._brightness_value)

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

    def clear(self):
        """Clear the variables to make every time auto optimization triggered independent."""
        self._pre_weighted_value = None
        self._base_value = None
        self._brightness_value = None

# outer utilities

def _weighted_sum(*number_and_weights: Tuple[float, float]) -> float:
    """Returns the weighted sum of each (number, weight) pair."""
    weighted_sum: float = 0
    for num, weight in number_and_weights:
        weighted_sum += num * weight
    return weighted_sum

def clamp(num: float, min: float, max: float) -> float:
    """Returns the clamped value within given boundary."""
    if num < min:
        return min
    elif num > max:
        return max
    else:
        return num