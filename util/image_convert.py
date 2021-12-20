import numpy as np
from PyQt5.QtGui import QImage, QPixmap

from util.image_type import ColorImage


def qpixmap_to_ndarray(image: QPixmap) -> ColorImage:
    """Converts the QPixmap type image to ndarray type."""
    qimage: QImage = image.toImage()

    width, height = qimage.width(), qimage.height()

    byte_str: bytes = qimage.constBits().asstring(height * width * 4)
    ndarray: ColorImage = np.frombuffer(byte_str, np.uint8).reshape((height, width, 4))

    return ndarray


def ndarray_to_qimage(image: ColorImage) -> QImage:
    height, width, channel = image.shape
    # RGB -> 3
    bytes_per_line = 3 * width

    return QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
