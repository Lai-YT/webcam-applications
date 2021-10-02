import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication


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


if __name__ == "__main__":
    screenshot = cv2.resize(qpixmap_to_ndarray(take_screenshot()), (640, 360))
    cv2.imshow("screenshot", screenshot)
    cv2.waitKey(0)
