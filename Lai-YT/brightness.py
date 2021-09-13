import cv2
import numpy as np
import screen_brightness_control as sbc
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QSlider, QVBoxLayout, QWidget

import gui.img.icon
from gui.component import ActionButton, Label
from lib.image_type import ColorImage


class BrightnessCalculator:
    @staticmethod
    def get_image_brightness(image: ColorImage, percentage: bool = False) -> float:
        """Returns the mean of brightness of the image,
        which is between 0 and 255.

        Arguments:
            image (NDArray[(Any, Any, 3), UInt8])
            percentage (bool): If True, brightness is in form of (mean / 255) * 100%. False in default
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        # hue, saturation, value
        # Value is as known as brightness.
        h, s, v = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel

        return 100 * v.mean() / 255

    @staticmethod
    def calculate_proper_screen_brightness(image: ColorImage) -> int:
        """Returns the suggested screen brightness value,
        which is between 0 and 100.

        Arguments:
            image (NDArray[(Any, Any, 3), UInt8])
        """
        brightness_percentage: float = BrightnessCalculator.get_image_brightness(image, percentage=True)

        if brightness_percentage >= 50:
            brightness = 0.8 * brightness_percentage
        elif brightness_percentage >= 30:
            brightness = 2 * (brightness_percentage - 30)
        else:
            brightness = 0

        return int(brightness)


class SliderDemo(QWidget):
    s_exit = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Utimate Brightness Detector")
        self.resize(450, 300)
        self.setWindowIcon(QIcon(":sun.ico"))
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self._set_slider()
        self._set_button()
        self.adjust_screen_brightness(20)
        self._connect_signal()
        # Initialize exit flag.
        self.exit_flag = False

    def adjust_screen_brightness(self, brightness: int):
        """Adjust the brightness of the screen and update the text."""
        self.label.setText(f"Brightness: {brightness}")
        # Slider should sync with the brightness.
        self.slider.setValue(brightness)
        sbc.set_brightness(brightness, method="wmi")

    @pyqtSlot()
    def capture_image(self):
        """Capture images and adjust the brightness instantly."""
        cam = cv2.VideoCapture(0)
        while not self.exit_flag:
            _, frame = cam.read()
            frame = cv2.flip(frame, flipCode=1) # horizontally flip

            brightness = BrightnessCalculator.calculate_proper_screen_brightness(frame)
            self.adjust_screen_brightness(brightness)

            cv2.imshow("Video Capture", frame)
            cv2.waitKey(50)

        # clean up
        cam.release()
        cv2.destroyAllWindows()
        self.s_exit.emit()

    def _set_slider(self):
        """Set a horizontal slider and a label on the window."""
        self.label = Label(f"Brightness: {sbc.get_brightness(method='wmi')}", font_size=35)
        self.layout.addWidget(self.label, alignment=Qt.AlignCenter, stretch=2)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 60)
        self.slider.setSingleStep(3)
        self.slider.setTickPosition(QSlider.TicksBelow)
        self.slider.setTickInterval(5)
        self.layout.addWidget(self.slider, stretch=2)

        self.slider.valueChanged.connect(
            lambda: self.adjust_screen_brightness(self.slider.value()))

    def _set_button(self):
        """Set a capture button on the window."""
        self.start = ActionButton("Start Capturing")
        self.start.clicked.connect(self._click_start)

        self.exit = ActionButton("Exit")
        self.exit.setEnabled(False)
        self.exit.clicked.connect(self._click_exit)

        self.layout.addWidget(self.start, alignment=Qt.AlignCenter, stretch=1)
        self.layout.addWidget(self.exit, alignment=Qt.AlignCenter, stretch=1)

    def _click_start(self):
        """Do things after start button is clicked."""
        self.slider.hide()
        self.exit.setEnabled(True)
        self.start.setEnabled(False)
        self.capture_image()

    def _click_exit(self):
        """Set exit flag to True."""
        self.exit_flag = True

    def _connect_signal(self):
        """Connect the exit signal and close the gui."""
        self.s_exit.connect(self.close)


if __name__ == "__main__":
    import sys

    from PyQt5.QtWidgets import QApplication


    app = QApplication(sys.argv)
    demo = SliderDemo()
    demo.show()
    sys.exit(app.exec_())
