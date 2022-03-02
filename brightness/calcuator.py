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

    def __init__(self, mode: BrightnessMode, base_value: int) -> None:
        self._mode = mode
        self._pre_base_value: int = base_value
        # Used to weight with new frame value to prevent
        # dramatical change of brightness.
        self._pre_weighted_value: float = 0
        # New brightness will be determined based on previous value, and
        # fine-tuned by difference of weighted value and base value.
        self._pre_brightness_value: int = base_value

    @property
    def mode(self) -> BrightnessMode:
        return self._mode

    @mode.setter
    def mode(self, new_mode: BrightnessMode) -> None:
        self._mode = new_mode

    def calculate_proper_screen_brightness(
            self,
            new_base_value: int,
            frames: Dict[BrightnessMode, ColorImage]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            new_base_value:
                The base value of brightness (The value of the slider).
            frames:
                The frame of the corresponding brightness mode.
                If mode is BOTH, there should have two frames;
                if is MANUAL, would be ignored.
        """
        self._new_base_value = new_base_value

        if self._mode is BrightnessMode.MANUAL:
            self._pre_base_value = self._new_base_value
            return self._new_base_value

        self._frames = frames

        self._calculate_frame_brightness()
        self._calculate_new_weighted_value()
        self._calculate_value_difference()
        self._calculate_brightness_value()

        self._set_pre_values_as_new_ones()

        return self._new_brightness_value

    def _calculate_frame_brightness(self) -> None:
        if self._mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            webcam_frame_brightness: float = (
                self.get_brightness_percentage(
                    self._frames[BrightnessMode.WEBCAM]
                )
            )
            # BOTH mode will overwrite this
            self._frame_brightness = webcam_frame_brightness
        if self._mode in (BrightnessMode.COLOR_SYSTEM, BrightnessMode.BOTH):
            screenshot_brightness: float = (
                self.get_brightness_percentage(
                    self._frames[BrightnessMode.COLOR_SYSTEM]
                )
            )
            self._frame_brightness = screenshot_brightness
        if self._mode is BrightnessMode.BOTH:
            # Webcam frame takes the lead. To protect one's eye,
            # the brighter the system is, the darker the result should be.
            weighted_frame_brightness: float = (
                webcam_frame_brightness * 0.6
                + (100 - screenshot_brightness) * 0.4
            )
            self._frame_brightness = weighted_frame_brightness

    def _calculate_new_weighted_value(self) -> None:
        # New frame brightness has the weight of 0.4 while the remaining
        # is on previous weighted value.
        self._new_weighted_value = (
            self._frame_brightness * 0.4 + self._pre_weighted_value * 0.6
        )

    def _calculate_value_difference(self) -> None:
        self._base_value_diff = self._new_base_value - self._pre_base_value
        self._weighted_value_diff = (
            self._new_weighted_value - self._pre_weighted_value
        )

    def _calculate_brightness_value(self) -> None:
        # Add value difference effect as offset on new brightness value.
        # Higher the brightness if the surrounding light is bright to keep the
        # screen clear and lower the brightness if the display on the screen is
        # light colored to reduce contrast of light.
        if self._mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            brightness_value = (
                self._pre_brightness_value
                + self._base_value_diff + self._weighted_value_diff * 0.35
            )
        elif self._mode is BrightnessMode.COLOR_SYSTEM:
            brightness_value = (
                self._pre_brightness_value
                + self._base_value_diff - self._weighted_value_diff * 0.45
            )
        self._new_brightness_value = int(_clamp(brightness_value, 0, 100))

    def _set_pre_values_as_new_ones(self) -> None:
        self._pre_base_value = self._new_base_value
        self._pre_weighted_value = self._new_weighted_value
        self._pre_brightness_value = self._new_brightness_value

    @staticmethod
    def get_brightness_percentage(frame: ColorImage) -> float:
        """Returns the mean of value channel, which represents the average
        brightness of the frame.

        Arguments:
            frame: The image to perform brightness calculation on.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        *_, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        return 100 * value.mean() / 255


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
