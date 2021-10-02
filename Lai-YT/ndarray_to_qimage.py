import sys

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QImage, QPixmap
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget
from cv2 import VideoCapture


class PhotoDisplayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(640, 500)

        self._layout = QVBoxLayout()
        self.setLayout(self._layout)

        self._create_label_for_photo()
        self._create_button_for_new_photo()
        self._connect_signals()

    def _create_label_for_photo(self):
        self._photo_label = QLabel()
        self._layout.addWidget(self._photo_label)

    def _create_button_for_new_photo(self):
        self._new_button = QPushButton("new photo")
        self._new_button.setFont(QFont("Arial", 18))
        self._layout.addWidget(self._new_button, alignment=Qt.AlignRight)

    def _connect_signals(self):
        self._new_button.clicked.connect(self._take_photo)

    def _take_photo(self):
        cam = VideoCapture(0)
        _, photo = cam.read()
        photo = self.ndarray_to_qimage(photo)
        self._photo_label.setPixmap(
            QPixmap.fromImage(photo).scaled(640, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        cam.release()

    @staticmethod
    def ndarray_to_qimage(photo):
        height, width, channel = photo.shape
        # RGB -> 3
        bytes_per_line = 3 * width

        return QImage(photo.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()


if __name__ == "__main__":
    app = QApplication([])
    window = PhotoDisplayer()
    window.show()
    sys.exit(app.exec_())
