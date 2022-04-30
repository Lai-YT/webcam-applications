from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from util.image_convert import qpixmap_to_ndarray
from util.image_type import ColorImage


def get_screenshot() -> ColorImage:
    screenshot: QPixmap = QApplication.primaryScreen().grabWindow(
        QApplication.desktop().winId()
    )
    return qpixmap_to_ndarray(screenshot)
