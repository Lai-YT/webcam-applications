import color_lib
import cv2
import numpy as np

from PyQt5.QtWidgets import QApplication


def get_dominant_color(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    maxsum = -100
    color = None
    color_dict = color_lib.getColorList()
    for d in color_dict:
        mask = cv2.inRange(hsv, color_dict[d][0], color_dict[d][1])
        binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
        binary = cv2.dilate(binary, None, iterations=2)
        cnts = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
        sum = 0
        for c in cnts:
            sum += cv2.contourArea(c)
        if sum > maxsum :
            maxsum = sum
            color = d

    return color


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
    ndarray = np.frombuffer(byte_str, np.uint8).reshape((height, width, 4))

    return ndarray

if __name__ == '__main__':
    screenshot = cv2.resize(qpixmap_to_ndarray(take_screenshot()), (1440, 810))
    cv2.imshow("screenshot", screenshot)
    dominant_color = get_dominant_color(screenshot)
    print(f"Dominant color: {dominant_color}")
    cv2.waitKey(0)