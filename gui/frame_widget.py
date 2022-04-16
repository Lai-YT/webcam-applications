from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import QLabel, QWidget

from gui.language import Language


class FrameWidget(QLabel):
    def __init__(self, parent: QWidget = None) -> None:
        super().__init__(parent)
        self.setStyleSheet("border: 1px solid black;")

    @pyqtSlot(QImage)
    def set_frame(self, frame: QImage) -> None:
        """Sets frame to the widget in respect of the size of widget if
        the widget is visible.

        Arguments:
            frame: The image to be set.
        """
        if not self.isVisible():
            # to save efficiency
            return
        # This is a self-adjust way.
        # NOTE: If simply use self.frameGeometry().width(), the image will grow.
        #   Because the image is always as big as the widget and PyQt will
        #   always give us a bigger widget, unstoppable.
        self.setPixmap(QPixmap.fromImage(frame).scaled(
            self.frameGeometry().width()  - 10,
            self.frameGeometry().height() - 10,
            Qt.KeepAspectRatio
        ))

    def change_language(self, lang: Language) -> None:
        # frame widget has no text
        pass
