from enum import Enum, auto
from typing import Any, Dict, Optional, Tuple

import cv2

from util.image_type import ColorImage


class BrightnessMode(Enum):
    """The modes that BrightnessCalculator uses."""
    WEBCAM = auto()
    COLOR_SYSTEM = auto()
    BOTH = auto()
    MANUAL = auto()


class BrightnessCalculator:
    """Handles processes which require value modulation."""

    def __init__(self) -> None:
        # Used to weight with new frame value to prevent
        # dramatical change of brightness.
        self._pre_weighted_value: Optional[float] = None
        # Current slider value.
        self._base_value: Optional[int] = None
        # Current screen brightness value.
        # New brightness will be determined based on this value, and fine-tuned
        # by difference of weighted value and base value.
        self._brightness_value: Optional[float] = None

    def calculate_proper_screen_brightness(
            self,
            mode: BrightnessMode,
            cur_base_value: int,
            frames: Dict[BrightnessMode, ColorImage]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode: The attribute determining which alogorithm to use for calculation.
            cur_base_value:
                The base value of brightness (The value of the slider).
            frames:
                The frame of the corresponding brightness mode.
                If mode is BOTH, there should have two frames.
        """
        self._cur_base_value: int = cur_base_value
        self._set_base_and_brightness_value_by_cur_base_if_first_call()

        self._calculate_new_weighted_value(mode, frames)
        self._calculate_value_diff()
        self._calculate_brightness_value(mode)

        self._set_pre_values_as_new_ones()

        return self._brightness_value

    def _set_base_and_brightness_value_by_cur_base_if_first_call(self) -> None:
        if self._base_value is None:
            self._base_value = self._cur_base_value
        if self._brightness_value is None:
            self._brightness_value = self._cur_base_value

    def _calculate_value_diff(self) -> None:
        self._base_value_diff: int = self._cur_base_value - self._base_value
        self._weighted_value_diff: float = self._new_weighted_value - self._pre_weighted_value

    def _calculate_new_weighted_value(
            self,
            mode: BrightnessMode,
            frames: Dict[BrightnessMode, ColorImage]) -> None:
        # Prepare the brightness precentage of the frame(s) that will be used
        # under the corresponding mode.
        if mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            webcam_frame_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.WEBCAM])
        if mode in (BrightnessMode.COLOR_SYSTEM, BrightnessMode.BOTH):
            screenshot_brightness: int = BrightnessCalculator.get_brightness_percentage(frames[BrightnessMode.COLOR_SYSTEM])
        if mode is BrightnessMode.BOTH:
            # Webcam frame takes the lead. To protect one's eye,
            # the brighter the system is, the darker the result should be.
            weighted_frame_brightness: float = (
                webcam_frame_brightness * 0.6
                + (100-screenshot_brightness) * 0.4
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
        self._new_weighted_value = new_weighted_value

    def _calculate_brightness_value(self, mode: BrightnessMode) -> None:
        # Add value difference effect as offset on new brightness value.
        # Higher the brightness if the surrounding light is bright to keep the
        # screen clear and lower the brightness if the display on the screen is
        # light colored to reduce contrast of light.
        if mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            self._brightness_value += self._base_value_diff + self._weighted_value_diff * 0.35
        elif mode is BrightnessMode.COLOR_SYSTEM:
            self._brightness_value += self._base_value_diff - self._weighted_value_diff * 0.45
        self._brightness_value = int(_clamp(self._brightness_value, 0, 100))

    def _set_pre_values_as_new_ones(self) -> None:
        self._base_value = self._cur_base_value
        self._pre_weighted_value = self._new_weighted_value

    @staticmethod
    def get_brightness_percentage(frame: ColorImage) -> int:
        """Returns the mean of value channel, which represents the average brightness
           of the frame.

        Arguments:
            frame: The image to perform brightness calculation on.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        *_, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        return int(100 * value.mean() / 255)

    def reset(self) -> None:
        """Resets the attributes to make optimizing method triggered
        independently every time.
        """
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
