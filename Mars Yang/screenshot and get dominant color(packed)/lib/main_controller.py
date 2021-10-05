import cv2
import numpy as np

from PyQt5.QtCore import QObject
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from lib.domiant_color_detector import DominantColorDetector
from lib.main_window import MainWindow

class MainController(QObject):

    def __init__(self, gui: MainWindow):
        super().__init__()

        self._gui = gui

        self._connect_signals()

    def _connect_signals(self):
        # Connect the siganls among widgets.
        self._gui.button.clicked.connect(self._click_start)
    
    def _click_start(self):
        screenshot = self._take_screenshot()
        dominant_color = DominantColorDetector.get_dominant_color(screenshot)
        colorfulness = DominantColorDetector.get_colorfulness(dominant_color)
        cv2.imshow(f"screenshot", screenshot)

    def _take_screenshot(self) -> np.ndarray:
        """Take a screenshot and convert the image to NDArray type."""
        # Have a QScreen instance to grabWindow with.
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(QApplication.desktop().winId())

        return cv2.resize(self._qpixmap_to_ndarray(screenshot), (1440, 810))

    @staticmethod
    def _qpixmap_to_ndarray(image: QPixmap) -> np.ndarray:
        qimage = image.toImage()
        
        width = qimage.width()
        height = qimage.height()

        byte_str = qimage.constBits().asstring(height * width * 4)
        ndarray = np.frombuffer(byte_str, np.uint8).reshape((height, width, 4))

        # type: NDArray[(Any, Any, 3), UInt8]
        return ndarray