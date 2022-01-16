import sys
from typing import Optional

import cv2
import dlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
from imutils import face_utils
from nptyping import NDArray

from util.color import MAGENTA
from util.image_type import ColorImage


# See https://numpy.org/doc/stable/reference/generated/numpy.set_printoptions.html#numpy-set-printoptions
np.set_printoptions(threshold=sys.maxsize)


class ImageFilter:
    """Handles processes which filters the brightness of the image."""

    _face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()

    def __init__(self) -> None:
        self._image: Optional[ColorImage] = None
        self._faces: Optional[dlib.rectangles] = None
        self._brightness: float = 0

    def refresh_image(self, image: ColorImage) -> None:
        """Refreshes the image in the filter and starts the process of filtering."""
        self._image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # start process
        self._detect_face()
        self._get_brightness()

    def plot_image(self) -> None:
        """Plots the image and shows filtered brightness on the window."""
        title = f"Brightness: {self._brightness}"

        plt.imshow(self._image)
        plt.title(title)
        plt.show()

    def _detect_face(self) -> None:
        """Detects face in a image and stores data of the face."""
        self._faces = self._face_detector(self._image)

    def _get_brightness(self) -> None:
        """Returns the filtered mean of brightness of an image."""
        hsv = cv2.cvtColor(self._image, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel

        # array of "value" channel with face area masked
        masked_array = self._mask_face_area(value)
        self._brightness = round(100 * self._filtered_mean(masked_array) / 255, 2)

    def _generate_mask(self, array: NDArray) -> NDArray:
        """Gets the boundaries of face area and generates the array with
        corresponding elements masked.
        """
        # Note: The size of the mask should be the same as a single channel of
        # an image, passing the size of self._image leads to size error because
        # its size is three times larger than the "value" channel of hsv.
        if self._faces is None:
            raise ValueError("please refresh the image first")
        if len(self._faces) != 1:
            raise ValueError("multiple faces aren't allowed")

        fx, fy, fw, fh = face_utils.rect_to_bb(self._faces[0])
        cv2.rectangle(self._image, (fx, fy), (fx+fw, fy+fh), MAGENTA, 1)

        # generate mask with face area masked
        mask = np.zeros(array.shape, dtype=np.bool8)
        mask[fy:fy+fh+1, fx:fx+fw+1] = 1
        return mask

    def _mask_face_area(self, array: NDArray) -> NDArray:
        mask = self._generate_mask(array)
        return ma.masked_array(array, mask)

    @staticmethod
    def _filtered_mean(masked_array: NDArray) -> float:
        """Filter out the brightest and darkest 5% area of a masked image."""
        unmasked = masked_array.compressed()
        unmasked.sort()
        return unmasked[int(unmasked.size * 0.05):int(unmasked.size * 0.95)].mean()
