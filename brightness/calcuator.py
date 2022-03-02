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
        self._base_value: int = base_value
        # Used to weight with new frame value to prevent
        # dramatical change of brightness.
        self._pre_weighted_value: float = 0
        # New brightness will be determined based on previous value, and
        # fine-tuned by difference of weighted value and base value.
        self._pre_brightness_offset: int = 0

    def get_mode(self) -> BrightnessMode:
        return self._mode

    def set_mode(self, new_mode: BrightnessMode) -> None:
        self._mode = new_mode

    def update_base_value(self, new_base_value: int) -> None:
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
        if self._mode is BrightnessMode.MANUAL:
            return self._base_value

        self._frames = frames

        self._calculate_frame_brightness()
        self._calculate_weighted_value()
        self._calculate_weighted_difference()
        self._calculate_brightness_offset()

        self._set_pre_values_as_new_ones()

        return int(self._clamp_between_zero_and_hundred(
                    self._base_value + self._new_brightness_offset
                ))

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

    def _calculate_weighted_value(self) -> None:
        # New frame brightness has the weight of 0.4 while the remaining
        # is on previous weighted value.
        self._new_weighted_value = (
            self._frame_brightness * 0.4 + self._pre_weighted_value * 0.6
        )

    def _calculate_weighted_difference(self) -> None:
        self._weighted_value_diff = (
            self._new_weighted_value - self._pre_weighted_value
        )

    def _calculate_brightness_offset(self) -> None:
        # Add value difference effect as offset on new brightness value.
        # Higher the brightness if the surrounding light is bright to keep the
        # screen clear and lower the brightness if the display on the screen is
        # light colored to reduce contrast of light.
        if self._mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            brightness_offset = (
                self._pre_brightness_offset + self._weighted_value_diff * 0.35
            )
        elif self._mode is BrightnessMode.COLOR_SYSTEM:
            brightness_offset = (
                self._pre_brightness_offset - self._weighted_value_diff * 0.45
            )
        self._new_brightness_offset = int(brightness_offset)

    def _set_pre_values_as_new_ones(self) -> None:
        self._pre_weighted_value = self._new_weighted_value
        self._pre_brightness_offset = self._new_brightness_offset

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
