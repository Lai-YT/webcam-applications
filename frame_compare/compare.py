import time
import webbrowser

import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication
from nptyping import Float64, NDArray

from frame_compare.screenshot import get_screenshot
from util.image_type import GrayImage


def get_compare_slices(image: GrayImage) -> NDArray[(36,), Float64]:
    """Takes 6 x 6 equally spaced slices and gets their means of pixel values as
    comparison components.

    This method works regardless of monitor size.

    Returns:
        An numpy array with 36 values, value range from 0 ~ 255, each in type
        Float64, which allows you to make basic operations without overflowing.
    """
    h, w = image.shape
    h //= 12
    w //= 12
    # 144 slices in total, take 36 of them
    slices = [np.mean(image[h*i:h*(i+1), w*j:w*(j+1)]) for i in range(0, 12, 2) for j in range(0, 12, 2)]
    return np.array(slices, dtype=np.float64)


if __name__ == "__main__":
    app = QApplication([])
    editor: GrayImage = cv2.cvtColor(get_screenshot(), cv2.COLOR_BGR2GRAY)
    # open a new google website to create really different screenshots
    webbrowser.open_new_tab("https://www.google.com/")
    time.sleep(3)  # time for loading
    google: GrayImage = cv2.cvtColor(get_screenshot(), cv2.COLOR_BGR2GRAY)

    diff = get_compare_slices(editor) - get_compare_slices(google)
    print(diff)
