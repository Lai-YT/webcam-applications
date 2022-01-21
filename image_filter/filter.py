import sys
from typing import Any, Optional

import cv2
import dlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
from imutils import face_utils
from nptyping import NDArray, UInt8

from util.color import MAGENTA
from util.image_type import ColorImage


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
        self._image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        self._face = face
        # Value is as known as brightness.
        _, _, self._value = cv2.split(cv2.cvtColor(self._image, cv2.COLOR_BGR2HSV))

    def get_brightness(self, mask: bool = True) -> float:
        """Returns the filtered mean of brightness of the image.

        The brightness is rounded to two decimal places.

        Arguments:
            mask: Whether the brightest and darkest 5% area of the image is
                  excluded or not. True in default.
        """
        if self._face is None or self._value is None:
            raise ValueError("please refresh the image first")
        if mask:
            # array of "value" channel with face area masked
            masked_arr = self._get_value_with_face_masked()
            # compress the masked array to truncate masked constants
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
        if self._face.is_empty():
            # all-pass for a no face image
            face_mask = np.zeros(self._value.shape, dtype=np.bool8)
        else:
            fx, fy, fw, fh = face_utils.rect_to_bb(self._face)
            # generate mask with face area masked
            face_mask = np.zeros(self._value.shape, dtype=np.bool8)
            face_mask[fy:fy+fh+1, fx:fx+fw+1] = 1
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
        array.sort()
        return array[int(array.size * 0.05):int(array.size * 0.95)].mean()


def plot_mask_diff(filter: ImageFilter) -> None:
    """Plots the image and shows filtered brightness on the window."""
    masked = filter.get_brightness()
    without_mask = filter.get_brightness(mask=False)
    diff = masked - without_mask

    title = (f"Brightness without mask: {without_mask}\n"
             f"Result brightness: {masked} (diff = {diff:.2f})")

    plt.imshow(filter.image)
    plt.title(title)
    plt.show()
