import cv2
from enum import Enum, auto

import matplotlib.pyplot as plt


class Mode(Enum):
    MEAN = auto()
    GAUSSIAN = auto()
    BILATERAL = auto()

def filter_image(img, mode: Mode):
    """Filter an image in corresponding mode, and return a list of images,
    which contains the original image and filtered image."""
    img_copy = img

    if mode is Mode.MEAN:
        filtered_image = cv2.blur(img_copy, (35, 35))
    elif mode is Mode.GAUSSIAN:
        filtered_image = cv2.GaussianBlur(img_copy, (35, 35), 0)
    elif mode is Mode.BILATERAL:
        filtered_image = cv2.bilateralFilter(img_copy, d=0, sigmaColor=100, sigmaSpace=15)
    return [img, filtered_image]

def get_brightness(image):
    """Returns the mean of brightness of an image.

        Arguments:
            image: The image to perform brightness calculation on.
        """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Value is as known as brightness.
    hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
    return int(100 * value.mean() / 255)

def plot_image(images):
    """Plot images before and after filtered."""
    titles = [
        f"Original Image\n Brightness: {get_brightness(images[0])}", 
        f"Filtered Image\n Brightness: {get_brightness(images[1])}"
    ]    
    for i in range(2):
        plt.subplot(1, 2, i+1), plt.imshow(images[i])
        plt.title(titles[i])
        plt.xticks([]), plt.yticks([])
    plt.show()
