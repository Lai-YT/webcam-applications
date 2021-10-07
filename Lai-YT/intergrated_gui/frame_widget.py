from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QLabel


class FrameWidget(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: 1px solid black;")

    def set_frame(self, frame, scale=None) -> None:
        """Sets frame to the widget.

        Arguments:
            frame (QPixmap): The image to be set.
            scale (Tuple[int, int]): Height and width. If is set, the frame is resized.
        """
        if scale is None:
            scale = (frame.width(), frame.height())
        self.setPixmap(frame.scaled(*scale))
