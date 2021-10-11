from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QLabel


class FrameWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: 1px solid black;")

    @pyqtSlot(QImage)
    def set_frame(self, frame: QImage) -> None:
        """Sets frame to the widget in respect of the size of widget.

        Arguments:
            frame (QImage): The image to be set.
        """
        # This is a self-adjust way.
        # If simply use self.frameGeometry().width(), the image will grow.
        # Because the image is always as big as the widget and PyQt will always
        # give use a bigger widget, unstoppable.
        self.setPixmap(QPixmap.fromImage(frame).scaled(
            self.frameGeometry().width()-10,
            self.frameGeometry().height()-10,
            Qt.KeepAspectRatio
        ))
