import dlib
import numpy as np
import numpy.ma as ma
from tkinter import BOTH
from enum import Enum, auto
from imutils import face_utils
from nptyping import NDArray
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
        # Used to weight with current frame value to prevent
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
            current_base_value: int,
            frames: Dict[BrightnessMode, ColorImage],
            face: Optional[dlib.rectangle]) -> int:
        """Returns the suggested screen brightness value, which is between 0 and 100.

        Arguments:
            mode: The attribute determining which alogorithm to use for calculation.
            current_base_value:
                The base value of brightness (The value of the slider).
            frames:
                The frame of the corresponding brightness mode.
                If mode is BOTH, there should have two frames.
        """
        # Set the values by current value passed in the first call.
        if self._base_value is None:
            self._base_value = current_base_value
        if self._brightness_value is None:
            self._brightness_value = current_base_value

        new_weighted_value = self._get_new_weighted_value(mode, frames, face)

        # Get diff values that will be added to the current value later.
        base_value_diff: float = current_base_value - self._base_value
        weighted_value_diff: float = new_weighted_value - self._pre_weighted_value

        self._update_current_value(mode, base_value_diff, weighted_value_diff)

        # Set previous values as current ones.
        self._base_value = current_base_value
        self._pre_weighted_value = new_weighted_value

        return int(self._brightness_value)

    def _get_new_weighted_value(self, 
                                mode: BrightnessMode, 
                                frames: Dict[BrightnessMode, ColorImage],
                                face: Optional[dlib.rectangle]) -> float:
        # Get new value that will be involved in the weighting process later.
        new_value = self._get_new_value(mode, frames, face)
        
        # Weight new value and previous weighted value to get new weighted value.
        new_weighted_value: float
        if self._pre_weighted_value is None:
            # New weighted value should be set the same value as frame_brightness
            # if no previous weighted value.
            new_weighted_value = new_value
            # avoid NoneType Error while computing offset
            self._pre_weighted_value = new_weighted_value
        else:
            new_weighted_value = new_value * 0.4 + self._pre_weighted_value * 0.6
        
        return new_weighted_value

    def _get_new_value(self, 
                       mode: BrightnessMode,
                       frames: Dict[BrightnessMode, ColorImage],
                       face: Optional[dlib.rectangle]) -> float:
        """Returns the value that will be involved in the weighting process."""
        frame_value: float
        screenshot_value: float
        new_value: float

        # calculate the brightness of webcam frame
        if mode in (BrightnessMode.WEBCAM, BrightnessMode.BOTH):
            if face is not None:
                frame_value = self._get_brightness(frames[BrightnessMode.WEBCAM], face)
            else:
                frame_value = self._get_brightness(frames[BrightnessMode.WEBCAM])

        # calculate the brightness of screenshot
        if mode in (BrightnessMode.COLOR_SYSTEM, BrightnessMode.BOTH):
            screenshot_value = 100 - self._get_brightness(
                frames[BrightnessMode.COLOR_SYSTEM]
            )

        # check mode and return corresponding value
        if mode is BrightnessMode.WEBCAM:
            new_value = frame_value
        elif mode is BrightnessMode.COLOR_SYSTEM:
            new_value = screenshot_value
        else: # BOTH
            new_value = 0.7 * frame_value + 0.3 * screenshot_value
        return new_value

    def _update_current_value(self,
                              mode: BrightnessMode,
                              base_value_diff: int,
                              weighted_value_diff: float) -> None:
        # After getting two diff values, add them with corresponding weight as offset 
        # on previous brightness value.
        if mode is BrightnessMode.BOTH:
            self._brightness_value += base_value_diff + weighted_value_diff * 0.4
        else:
            self._brightness_value += base_value_diff + weighted_value_diff * 0.3
        # Value over boundary will be returned as boundary value.
        self._brightness_value = _clamp(self._brightness_value, 0, 100)

    def _get_brightness(self, 
                        frame: ColorImage,
                        face: Optional[dlib.rectangle] = None) -> int:
        """Returns the mean of value channel, which represents the average brightness
           of the frame.

        Arguments:
            frame: The image to perform brightness calculation on.
        """
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        *channel, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel

        if face is not None:
            mask = self._generate_face_mask(face, value.shape)
            masked_arr = ma.masked_array(value, mask)
            # truncate masked constants
            value = masked_arr.compressed()
        return int(100 * value.mean() / 255)

    def _generate_face_mask(self, face: Optional[dlib.rectangle], frame_shape) -> NDArray:
        """Gets the boundaries of face area and generates the value with
        corresponding elements masked.
        """
        # get the four corners of face
        fx, fy, fw, fh = face_utils.rect_to_bb(face)
        # generate mask with face area masked
        face_mask = np.zeros(frame_shape, dtype=np.bool8)
        face_mask[fy:fy+fh+1, fx:fx+fw+1] = True
        return face_mask

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
