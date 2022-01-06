from enum import Enum, auto
from typing import Tuple

import cv2
import matplotlib.pyplot as plt

from image_filter.mask import get_brightness
from util.image_type import ColorImage


class FilterMode(Enum):
    MEAN = auto()
    GAUSSIAN = auto()
    BILATERAL = auto()


def filter_image(raw_image: ColorImage, mode: FilterMode) -> Tuple[ColorImage, ColorImage]:
    """Filters an image in corresponding mode, and return a list of images,
    which contains the original image and filtered image.
    """
    img_copy = raw_image.copy()

    filtered_image: ColorImage
    if mode is FilterMode.MEAN:
        filtered_image = cv2.blur(img_copy, (75, 75))
    elif mode is FilterMode.GAUSSIAN:
        filtered_image = cv2.GaussianBlur(img_copy, (35, 35), 0)
    elif mode is FilterMode.BILATERAL:
        filtered_image = cv2.bilateralFilter(img_copy, d=0, sigmaColor=100, sigmaSpace=15)
    return (raw_image, filtered_image)


def plot_images(images: ColorImage) -> None:
    """Plots images before and after filtered."""
    titles = [
        f"Original Image\n Brightness: {get_brightness(images[0])}",
        f"Filtered Image\n Brightness: {get_brightness(images[1])}",
    ]
    for i in range(2):
        plt.subplot(1, 2, i+1)
        plt.imshow(images[i])
        plt.title(titles[i])
    plt.show()
