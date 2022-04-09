import sys
from datetime import datetime
from typing import Any

import cv2
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from util.image_convert import qpixmap_to_ndarray
from util.image_type import ColorImage
from util.path import to_abs_path


def get_screenshot() -> ColorImage:
    screenshot: QPixmap = QApplication.primaryScreen().grabWindow(
        QApplication.desktop().winId()
    )
    return qpixmap_to_ndarray(screenshot)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    screenshot = get_screenshot()
    cv2.imshow("screenshot", screenshot)
    cv2.waitKey()

    if len(sys.argv) == 2 and sys.argv[1] == "save":
        cv2.imwrite(to_abs_path(f"./screenshot-{datetime.now().strftime('%Y%m%d-%H%M%S')}.jpg"), screenshot)
