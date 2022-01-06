from typing import Any

import cv2
import numpy as np
import numpy.ma as ma
from nptyping import NDArray

from util.image_type import ColorImage


def filtered_mean(ndarray: NDArray[(Any, Any), Any]) -> float:
    """Makes the 2-dimensional array flat, then calculates the mean on its
    values except the top 10% biggest values (filtered).
    """
    # axis=None does the flatten
    sorted_arr: NDArray[(Any,), Any] = np.sort(ndarray, axis=None)
    # mask = np.ones(len(sorted_arr))
    # mask[:int(len(sorted_arr) * 0.9)] = 0
    # mx = ma.masked_array(sorted_arr, mask=mask)

    return sorted_arr[:int(len(sorted_arr) * 0.9)].mean()


def get_brightness(image: ColorImage, mask: bool = False) -> float:
    """Returns the mean of brightness of an image.

    Arguments:
        image: The image to perform brightness calculation on.
        mask:
            If mask is True, the brightest 10% area of the image
            will be filtered.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Value is as known as brightness.
    hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel

    if mask:
        brightness = 100 * filtered_mean(value) / 255
    else:
        brightness = 100 * value.mean() / 255

    return round(brightness, 2)
