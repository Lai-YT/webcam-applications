import math

import cv2
import numpy as np
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
from nptyping import Float, Int, NDArray

from util.image_convert import qpixmap_to_ndarray
from util.image_type import ColorImage, GrayImage


def get_screenshot() -> ColorImage:
    screenshot: QPixmap = QApplication.primaryScreen().grabWindow(
        QApplication.desktop().winId()
    )
    return qpixmap_to_ndarray(screenshot)


def get_compare_slices(image: ColorImage) -> NDArray[(36,), Float[64]]:
    """Takes 6 x 6 equally spaced slices and gets their means of pixel values as
    comparison components.

    This method works regardless of monitor size.

    Returns:
        An numpy array with 36 values, value range from 0 ~ 255, each in type
        Float64, which allows you to make basic operations without overflowing.
    """
    gray_image: GrayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    h, w = gray_image.shape
    h //= 12
    w //= 12
    # 144 slices in total, take 36 of them
    slices = [
        np.mean(gray_image[h * i : h * (i + 1), w * j : w * (j + 1)])
        for i in range(0, 12, 2)
        for j in range(0, 12, 2)
    ]
    return np.array(slices, dtype=np.float64)


def compare_similarity_of_slices(
    slices1: NDArray[(36,), Float], slices2: NDArray[(36,), Float]
) -> float:
    """Calculates how similar these 2 set of slices are by the RMS value of differece.

    Returns:
        the ratio of similarity between [0, 1], percisely 1 - RMS / 255,
        1 means they are the same.
    """
    # make sure no overflow
    diff = slices1.astype(np.float64) - slices2.astype(np.float64)
    rms = math.sqrt(sum(np.square(diff)) / 36)
    return 1 - rms / 255


if __name__ == "__main__":
    import time
    import webbrowser

    import matplotlib.pyplot as plt

    app = QApplication([])
    editor: ColorImage = get_screenshot()
    # open a new google website to create really different screenshots
    webbrowser.open_new_tab("https://www.google.com/")
    time.sleep(3)  # time for loading
    google: ColorImage = get_screenshot()

    diff: NDArray[(36,), Float[64]] = get_compare_slices(editor) - get_compare_slices(
        google
    )
    print("6 x 6 value diffs: ")
    print(diff)
    rms = math.sqrt(sum(np.square(diff)) / 36)
    print(f"RMS: {rms}")
    print(f"{1 - rms / 255:.1%}")

    fig, axs = plt.subplots(1, 2)
    axs[0].hist(editor.ravel(), range=(0, 255), bins=128)
    axs[1].hist(google.ravel(), range=(0, 255), bins=128)
    plt.setp(axs, ylim=max(ax.get_ylim() for ax in axs))
    plt.show()
