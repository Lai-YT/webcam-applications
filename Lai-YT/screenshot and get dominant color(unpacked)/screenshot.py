# reference: https://github.com/sunny-fang/SunnyFang-Collection/blob/cea68c9df1b07688424a6ba71167c9aac248cb9e/Graduate%20School/Python%20related/Main%20color%20analysis/%E4%B8%BB%E8%89%B2%E7%B3%BB%E5%88%86%E6%9E%90.py

import cv2
import numpy as np
from color_lib import COLOR_DICT

from PyQt5.QtWidgets import QApplication


def get_dominant_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    max_area = -1  # Since area won't be less than 0, -1 indicates the absolute minimum.
    dominant_color = None
    for color, bounds in COLOR_DICT.items():
        mask = cv2.inRange(hsv, *bounds)  # values in bound => 255, out of => 0
        binary = cv2.dilate(mask, None, iterations=2)

        # Get the contours that circles the colored areas.
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        # Calculate the total area of this color.
        # And store as the current dominant color if this color has the current max area.
        area = 0
        for cnt in contours:
            area += cv2.contourArea(cnt)
        if area > max_area:
            max_area = area
            dominant_color = color

    return dominant_color


def take_screenshot() -> "QPixmap":
    app = QApplication([])
    # Have a QScreen instance to grabWindow with.
    screen = QApplication.primaryScreen()
    screenshot = screen.grabWindow(QApplication.desktop().winId())

    return screenshot


def qpixmap_to_ndarray(image: "QPixmap") -> "NDArray[(Any, Any, 3), UInt8]":
    qimage = image.toImage()

    width = qimage.width()
    height = qimage.height()

    byte_str = qimage.constBits().asstring(height * width * 4)
    ndarray = np.frombuffer(byte_str, dtype=np.uint8).reshape((height, width, 4))

    return ndarray


if __name__ == "__main__":
    screenshot = cv2.resize(qpixmap_to_ndarray(take_screenshot()), (1440, 810))
    cv2.imshow("screenshot", screenshot)

    dominant_color = get_dominant_color(screenshot)
    print(f"Dominant color: {dominant_color}")
    cv2.waitKey(0)
