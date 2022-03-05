from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple

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
        self._base_value: int = base_value
        # Used to weight with new frame value to prevent
        # dramatical change of brightness.
        self._pre_weighted_value: float = 0
        # New brightness will be determined based on this value, and
        # fine-tuned by difference of weighted value and base value.
        self._brightness_value = float(base_value)
        # For thread-safety, a mode change is appended into the list instead of
        # directly writing to the variable.
        self._mode_change_list: List[BrightnessMode] = []

    def get_mode(self) -> BrightnessMode:
        return self._mode

    def set_mode(self, new_mode: BrightnessMode) -> None:
        self._mode_change_list.append(new_mode)

    def update_base_value(self, new_base_value: int) -> None:
        # an offset on base value directly reflects to the brightness value
        self._brightness_value += new_base_value - self._base_value
        self._base_value = new_base_value

    def calculate_proper_screen_brightness(
            self,
            frames: Dict[BrightnessMode, ColorImage]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            frames:
                The frame of the corresponding brightness mode.
                If mode is BOTH, there should have two frames;
                if is MANUAL, would be ignored.
        """
        self._check_mode_change()

        if self._mode is BrightnessMode.MANUAL:
            self._reset()
            return self._base_value

        self._frames = frames

        self._calculate_frame_value()
        self._calculate_weighted_value()
        self._calculate_weighted_difference()
        self._calculate_brightness_value()

        self._set_pre_values_as_new_ones()
        # Value over boundary will be returned as boundary value.
        return int(self._clamp_between_zero_and_hundred(self._brightness_value))

    def _check_mode_change(self) -> None:
        if self._mode_change_list:
            self._mode = self._mode_change_list.pop(0)

    def _calculate_frame_value(self) -> None:
        if self._mode in (BrightnessMode.WEBCAM, BrightnessMode.COLOR_SYSTEM):
            self._frame_value = self.get_brightness_percentage(self._frames[self._mode])
        else: # BOTH
            # Webcam frame takes the lead. To protect one's eye,
            # the brighter the system is, the darker the result should be.
            self._frame_value = (
                0.6 * self.get_brightness_percentage(self._frames[BrightnessMode.WEBCAM])
                + 0.4 * (100 - self.get_brightness_percentage(self._frames[BrightnessMode.COLOR_SYSTEM]))
            )

    def _calculate_weighted_value(self) -> None:
        self._new_weighted_value = (
            self._frame_value * 0.4 + self._pre_weighted_value * 0.6
        )

    def _calculate_weighted_difference(self) -> None:
        self._weighted_value_diff = (
            self._new_weighted_value - self._pre_weighted_value
        )

    def _calculate_brightness_value(self) -> None:
        # Higher the brightness if the surrounding light is bright to keep the
        # screen clear and lower the brightness if the display on the screen is
        # light colored to reduce contrast of light.
        if self._mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            factor = 0.35
        else:
            factor = -0.45
        self._brightness_value += self._weighted_value_diff * factor

    def _set_pre_values_as_new_ones(self) -> None:
        self._pre_weighted_value = self._new_weighted_value

    def _reset(self) -> None:
        # Sets the brightness back to base, and weighted value = 0 prevents
        # the value from immediate jump.
        self._pre_weighted_value = 0
        self._brightness_value = self._base_value

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

    @staticmethod
    def _clamp_between_zero_and_hundred(value: float) -> float:
        if value > 100:
            return 100
        if value < 0:
            return 0
        return value
