from enum import Enum, auto
from typing import Dict, List, Optional, Tuple

import cv2
import dlib
import numpy as np
import numpy.ma as ma
from imutils import face_utils
from nptyping import NDArray

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
        self._pre_weighted_value: Optional[float] = None
        # New brightness will be determined based on this value, and
        # fine-tuned by difference of weighted value and base value.
        self._brightness_value = float(base_value)
        # For thread-safety, a mode change is appended into the list instead of
        # directly writing to the variable.
        self._mode_change_list: List[BrightnessMode] = []
        # The flag will be set True when user changes mode.
        self._mode_change_flag: bool = False

    def get_mode(self) -> BrightnessMode:
        return self._mode

    def set_mode(self, new_mode: BrightnessMode) -> None:
        self._mode_change_list.append(new_mode)

    def update_base_value(self, new_base_value: int) -> None:
        # an offset on base value linearly reflects to the brightness value
        self._brightness_value += new_base_value - self._base_value
        self._base_value = new_base_value

    def calculate_proper_screen_brightness(
            self,
            frames: Dict[BrightnessMode, ColorImage],
            face: Optional[dlib.rectangle]) -> int:
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
        self._face = face

        self._calculate_new_value()
        self._calculate_weighted_value()
        self._calculate_weighted_difference()
        self._calculate_brightness_value()

        self._set_pre_values_as_new_ones()
        # Value over boundary will be returned as boundary value.
        return int(self._clamp_between_zero_and_hundred(self._brightness_value))

    def _check_mode_change(self) -> None:
        self._mode_change_flag = bool(self._mode_change_list)
        if self._mode_change_flag:
            self._mode = self._mode_change_list.pop(0)

    def _calculate_new_value(self) -> None:
        # calculate the brightness of webcam frame
        if self._mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            frame_value: float = BrightnessCalculator.get_brightness_percentage(
                self._frames[BrightnessMode.WEBCAM], self._face
            )

        # calculate the brightness of screenshot
        if self._mode in (BrightnessMode.COLOR_SYSTEM, BrightnessMode.BOTH):
            screenshot_value: float = 100 - BrightnessCalculator.get_brightness_percentage(
                self._frames[BrightnessMode.COLOR_SYSTEM]
            )

        new_value: float
        # check mode and return corresponding value
        if self._mode is BrightnessMode.WEBCAM:
            new_value = frame_value
        elif self._mode is BrightnessMode.COLOR_SYSTEM:
            new_value = screenshot_value
        else: # BOTH
            new_value = 0.7 * frame_value + 0.3 * screenshot_value
        self._new_value = new_value

    def _calculate_weighted_value(self) -> None:
        # When first frame passed or mode changed,
        # view the brightness of current frame as datum value.
        # That is, set both pre and new weighted value the same as
        # new value to make diff be 0.
        if self._pre_weighted_value is None or self._mode_change_flag:
            self._pre_weighted_value = self._new_value
            self._new_weighted_value = self._new_value
        else:
            self._new_weighted_value = (
                self._new_value * 0.4 + self._pre_weighted_value * 0.6
            )

    def _calculate_weighted_difference(self) -> None:
        if self._pre_weighted_value is None:
            raise ValueError("first frame pass not handled")
            
        self._weighted_value_diff = (
            self._new_weighted_value - self._pre_weighted_value
        )

    def _calculate_brightness_value(self) -> None:
        self._brightness_value += 0.3 * self._weighted_value_diff

    def _set_pre_values_as_new_ones(self) -> None:
        self._pre_weighted_value = self._new_weighted_value

    def _reset(self) -> None:
        # Sets the brightness back to base, and weighted value to None
        # to prevent the value from immediate jump.
        self._pre_weighted_value = None
        self._brightness_value = self._base_value

    @staticmethod
    def get_brightness_percentage(
            frame: ColorImage,
            face: Optional[dlib.rectangle] = None) -> float:
        """Returns the mean of value channel, which represents the average
        brightness of the frame.

        Arguments:
            frame: The image to perform brightness calculation on.
            face: If provided, the non-face area of the frame is masked.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        *_, value = cv2.split(hsv)

        if face is not None:
            mask = BrightnessCalculator._generate_face_mask(face, value.shape)
            masked_arr = ma.masked_array(value, mask)
            # truncate masked constants
            value = masked_arr.compressed()
        return 100 * value.mean() / 255

    @staticmethod
    def _generate_face_mask(
            face: Optional[dlib.rectangle],
            frame_shape: Tuple[int, int, int]) -> NDArray:
        """Gets the boundaries of face area and generates the value with
        corresponding elements masked.
        """
        # get the four corners of face
        fx, fy, fw, fh = face_utils.rect_to_bb(face)
        # generate mask with face area masked
        face_mask = np.zeros(frame_shape, dtype=np.bool8)
        face_mask[fy:fy+fh+1, fx:fx+fw+1] = True
        return face_mask

    @staticmethod
    def _clamp_between_zero_and_hundred(value: float) -> float:
        if value > 100:
            return 100
        if value < 0:
            return 0
        return value
