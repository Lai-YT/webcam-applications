import numpy as np
from PyQt5.QtGui import QImage


def qpixmap_to_ndarray(image: "QPixmap") -> "NDArray[(Any, Any, 3), UInt8]":
    qimage = image.toImage()

    width = qimage.width()
    height = qimage.height()

    byte_str = qimage.constBits().asstring(height * width * 4)
    ndarray = np.frombuffer(byte_str, np.uint8).reshape((height, width, 4))

    return ndarray


def ndarray_to_qimage(image: "NDArray[(Any, Any, 3), UInt8]") -> "QImage":
    height, width, channel = image.shape
    # RGB -> 3
    bytes_per_line = 3 * width

    return QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()
