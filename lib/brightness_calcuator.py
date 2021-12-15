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
        # Used to weight with frame brightness to reduce the effect of
        # brightness difference, which may cause dramatical value change of
        # brightness value.
        self._pre_weighted_value: Optional[float] = None
        # Store current slider value.
        # If slider value changes, get the difference of two values
        # and update base value.
        self._base_value: Optional[int] = None
        # Store current screen brightness value.
        # Every new frame generates a new offset of brightness, then the
        # process will add the offset to current brightness value,
        # emit the signal of value change, and update current brightness value.
        self._brightness_value: Optional[float] = None

    def calculate_proper_screen_brightness(
            self,
            mode: BrightnessMode,
            current_base_value: int,
            frames: Dict[BrightnessMode, ColorImage]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode: Mode affects algorithm used in calculation.
            current_base_value:
                The base value of brightness (The value of the slider).
            frames:
                Frame of the corresponding brightness mode.
                If mode is BOTH, there should have two frames.
        """
        # Take the values of the first time as the initial values.
        if self._base_value is None:
            self._base_value = current_base_value
        if self._brightness_value is None:
            self._brightness_value = current_base_value

        # Prepare the brightness precentage of the frame(s) that will be used
        # under the corresponding mode.
        if mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            webcam_frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.WEBCAM])
        if mode in (BrightnessMode.COLOR_SYSTEM, BrightnessMode.BOTH):
            screenshot_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.COLOR_SYSTEM])
        if mode is BrightnessMode.BOTH:
            # webcam frame takes the lead
            weighted_frame_brightness: float = (
                webcam_frame_brightness * 0.6 + (100-screenshot_brightness) * 0.4
            )

        # New frame brightness has the weight of 0.4 while the remaining
        # is on previous weighted value.
        weight_of_modes: Dict[BrightnessMode, Tuple[str, float]] = {
            BrightnessMode.WEBCAM: ("webcam_frame_brightness", 0.4),
            BrightnessMode.COLOR_SYSTEM: ("screenshot_brightness", 0.4),
            BrightnessMode.BOTH: ("weighted_frame_brightness", 0.4),
        }

        frame_brightness: float = locals()[weight_of_modes[mode][0]]
        brightness_weight: float = weight_of_modes[mode][1]
        new_weighted_value: float
        if self._pre_weighted_value is None:
            # No previous weighted value, so new weighted value should be set
            # the same value as frame_brightness
            new_weighted_value = frame_brightness * 1
            # Set previous weighted value as new weighted value
            # to avoid NoneType Error while computing offset.
            self._pre_weighted_value = new_weighted_value
        else:
            new_weighted_value = (
                frame_brightness * brightness_weight
                + self._pre_weighted_value * (1-brightness_weight)
            )
        # Both value differences affect the brightness value.
        base_value_diff: float = current_base_value - self._base_value
        weighted_value_diff: float = new_weighted_value - self._pre_weighted_value

        # Add value difference effect as offset on current brightness value.
        # Higher the brightness if the surrounding light is bright to keep the
        # screen clear and lower the brightness if the display on the screen is
        # light colored to reduce contrast of light.
        if mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            self._brightness_value += base_value_diff + weighted_value_diff * 0.25
        elif mode is BrightnessMode.COLOR_SYSTEM:
            self._brightness_value += base_value_diff - weighted_value_diff * 0.25
        self._brightness_value = _clamp(self._brightness_value, 0, 100)

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

    def reset(self) -> None:
        """Reset the variables to make every time auto optimization triggered independent."""
        self._pre_weighted_value = None
        self._base_value = None
        self._brightness_value = None


# outer utilities

def _clamp(value: float, v_min: float, v_max: float) -> float:
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
