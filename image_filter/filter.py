import sys
from typing import Any, Optional

import cv2
import dlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
from imutils import face_utils
from nptyping import Float32, NDArray, UInt8

from util.image_type import ColorImage


np.set_printoptions(threshold=sys.maxsize)

class ImageFilter:
    """Handles processes which filters the brightness of the image."""

    def __init__(self) -> None:
        self._image: Optional[ColorImage] = None
        self._face: Optional[dlib.rectangle] = None
        self._value: Optional[NDArray[(Any, Any), UInt8]] = None

    @property
    def image(self) -> ColorImage:
        return self._image

    def refresh_image(self, image: ColorImage, face: dlib.rectangle) -> None:
        """Refreshes the image in the filter and starts the process of filtering."""
        # init arguments
        self._image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self._face = face
        # Value is as known as brightness.
        *_, self._value = cv2.split(cv2.cvtColor(image, cv2.COLOR_BGR2HSV))

    def get_brightness(self, *, weight: bool = False, mask: bool = False) -> float:
        """Returns the mean of brightness of the image.

        Notice that mask and weight can't both be True.
        A simple filtered mean is used when both of them are False;
        mask-filtered mean when mask is True and weight is False;
        weighted mean when weight is True and mask is mean.
        Which filter means to exclude the brightest and darkest 5% area of the
        image.

        The brightness is rounded to two decimal places.

        Arguments:
            weight:
                Whether the face area and background area have different
                weightings. False in default.
            mask:
                Whether the face area of the image is excluded or not.
                False in default.
        """
        if mask & weight:
            raise ValueError("arguments mask and weight can't both be True")

        brightness: float
        if weight:
            brightness = self._get_weighted_brightness()
        else:
            brightness = self._get_filtered_brightness(mask)
        return brightness

    def _get_weighted_brightness(self) -> float:
        weighted_value = self._get_weighted_value()
        data_arr = weighted_value.flatten()
        return round(100 * np.sum(data_arr) / 255, 2)

    def _get_filtered_brightness(self, mask: bool = True) -> float:
        if self._value is None:
            raise ValueError("please refresh the image first")
        if mask:
            masked_arr = self._get_value_with_face_masked()
            # truncate masked constants
            data_arr = masked_arr.compressed()
        else:
            data_arr = self._value.flatten()
        return round(100 * self._filtered_mean(data_arr) / 255, 2)

    def _generate_face_mask(self) -> NDArray:
        """Gets the boundaries of face area and generates the value with
        corresponding elements masked.
        """
        # Note: The size of the mask should be the same as a single channel of
        # an image, passing the size of self._image leads to size error because
        # its size is three times larger than the "value" channel of hsv.
        if self._face is None or self._value is None:
            raise ValueError("please refresh the image first")
        if self._face.is_empty():
            # all-pass for a no face image
            face_mask = np.zeros(self._value.shape, dtype=np.bool8)
        else:
            fx, fy, fw, fh = face_utils.rect_to_bb(self._face)
            # generate mask with face area masked
            face_mask = np.zeros(self._value.shape, dtype=np.bool8)
            face_mask[fy:fy+fh+1, fx:fx+fw+1] = True
        return face_mask

    def _get_value_with_face_masked(self) -> NDArray:
        face_mask = self._generate_face_mask()
        return ma.masked_array(self._value, face_mask)

    @staticmethod
    def _filtered_mean(array: NDArray[(Any,), Any]) -> float:
        """Returns the mean of values with the brightest and darkest 5% area
        filtered out.

        Arguments:
            array: A 1-D to calculate mean on.
        """
        # not to modify the input array
        return np.sort(array)[int(array.size * 0.05):int(array.size * 0.95)].mean()

    def _get_weighted_value(self) -> NDArray[(Any, Any), Float32]:
        """Weights the value by area."""
        if self._face is None or self._value is None:
            raise ValueError("please refresh the image first")

        fx, fy, fw, fh = face_utils.rect_to_bb(self._face)

        # Weighting makes the data type not int anymore. Numpy automatically
        # upcast it to float64, but float32 is enough.
        value: NDArray[(Any, Any), Float32] = self._value.astype(np.float32)
        # weights of area outside and inside face are 4 and 6
        face_area = np.full(value.shape, 4, dtype=np.float32)
        face_area[fy:fy+fh+1, fx:fx+fw+1] = 6
        # divide by sum of weights
        return value * face_area / np.sum(face_area)


def plot_mask_diff(filter_: ImageFilter) -> None:
    """Plots the image and shows filtered brightness on the window."""
    masked = filter_.get_brightness(mask=True)
    without_mask = filter_.get_brightness()
    diff = masked - without_mask
    weighted = filter_.get_brightness(weight=True)

    title = (f"Brightness without mask: {without_mask}\n"
             f"Result brightness: {masked} (diff = {diff:.2f})\n"
             f"Weighted brightness: {weighted}")

    plt.imshow(filter_.image)
    plt.title(title)
    plt.show()
