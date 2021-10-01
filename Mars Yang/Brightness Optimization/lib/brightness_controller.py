import cv2
import numpy as np
import sys

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, Qt, QThread
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication
import screen_brightness_control as sbc

from lib.brightness_calculator import BrightnessCalculator
from lib.brightness_widget import BrightnessWidget, WarningWidget
from lib.task_worker import TaskWorker



method = "wmi"
class BrightnessController(QObject):
    # Emits when the `Exit` button is clicked.
    s_exit = pyqtSignal()

    def __init__(self, mode: str):
        super().__init__()

        self._mode = mode
        self._brightness_widget = BrightnessWidget()
        self._warning_widget = WarningWidget()
        # Since there are multiple fuctions that need to access camera,
        # make it an attribute instead of opening in a certain method.
        self.cam = cv2.VideoCapture(0)
        self._f_exit = False
        self._warning_flag = True

        self._connect_signals()
        self._advance_preparation()
        if self._mode == "color-system":
            print("Sorry, this part is not prepared yet.")
        else:
            self._run()

    def _run(self):
        """Moves the _capture_image process to another thread and start it."""
        self._thread = QThread()
        self._worker = TaskWorker(self._capture_image)
        self._worker.moveToThread(self._thread)
        # Worker starts running after the thread is started.
        self._thread.started.connect(self._worker.run)
        # The job of thread and worker is finished after the App. calls stop.
        self.s_exit.connect(self._thread.quit)
        self.s_exit.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _connect_signals(self):
        # Connect the siganls of the warning dialog.
        self._warning_widget.checkbox.toggled.connect(self._stop_warning)
        self._warning_widget.button.clicked.connect(self._close_dialog)
        # The slider has two states, depending on the action user takes.
        self._brightness_widget.checkbox.stateChanged.connect(self._update_brightness_and_slider_visibility)
        # Label and screen should be set when the user adjust the slider.
        self._brightness_widget.slider.valueChanged.connect(
            lambda: self._set_brightness(self._brightness_widget.slider.value(), set_slider=False))
        # Connect the exit signal.
        self.s_exit.connect(self._brightness_widget.close)

    @pyqtSlot(int)
    def _update_brightness_and_slider_visibility(self, check_state: int):
        """
        If the checkbox is checked, update the base values so can correctly
        calculate the brightness and hide the slider since is now automatic;
        otherwise, have the slider value match the current brightness and let
        users adjust brightness by themselves.
        """
        if check_state == Qt.Checked:
            self._update_base_brightness_values()
            self._brightness_widget.slider.hide()
        else:
            self._set_brightness(sbc.get_brightness(method=method), set_slider=True)
            self._brightness_widget.slider.show()

    def _advance_preparation(self):
        """Init the slider and label status to be as same as the user's screen brightness."""
        self._set_brightness(sbc.get_brightness(method=method), set_slider=True)
        self._update_base_brightness_values()

    def _capture_image(self):
        """Capture images and adjust the brightness instantly."""
        while not self._f_exit:
            _, frame = self.cam.read()
            frame = cv2.flip(frame, flipCode=1) # horizontally flip

            # If "Brightness Optimization" is checked, adjust the brightness automatically;
            # otherwise, users can adjust by themselves.
            if self._brightness_widget.checkbox.isChecked():
                self._brightness_widget.slider.hide()
                self._optimize_brightness(frame)
            else:
                self._brightness_widget.slider.show()
                self._warn_if_too_bright()

            cv2.waitKey(25)
        
        # Close the webcam and emit the exit signal.
        self.cam.release()
        cv2.destroyAllWindows()
        self.s_exit.emit()

    def _optimize_brightness(self, frame):
        """Control screen brightness automatically in two different modes."""
        # Screenshot and turn image type to np.array
        if self._mode == "color-system":
            screen = QtWidgets.QApplication.primaryScreen()
            # image type: pixmap
            image = screen.grabWindow(QApplication.desktop().winId())
            image = self._pixmap_to_image(image)

        brightness = BrightnessCalculator.calculate_proper_screen_brightness(self._mode, self._threshold, self._base_value, frame)
        self._set_brightness(brightness, set_slider=False)

    @staticmethod
    def _pixmap_to_image(image: QPixmap):
        ## Get the size of the current pixmap
        size = image.size()
        h = size.width()
        w = size.height()

        ## Get the QImage Item and convert it to a byte string
        qimg = image.toImage()
        byte_str = qimg.bits().tobytes()

        ## Using the np.frombuffer function to convert the byte string into an np array
        img = np.frombuffer(byte_str, dtype=np.uint8).reshape((w,h,4))

        return img

    def _warn_if_too_bright(self):
        # If screen brightness > 80, the warning dialog will pop out.
        if self._brightness_widget.slider.value() > 80 and self._warning_flag:
            self._brightness_widget.slider.setEnabled(False)
            self._brightness_widget.checkbox.setEnabled(False)
            self._warning_widget.show()

    def _set_brightness(self, brightness: int, set_slider: bool):
        """Adjust the brightness of the screen manually or automatically.

        Arguments:
            brightness (int): The brightness value to set to the screen
            set_slider (bool): The value of slider will also be set is True
        """
        if set_slider:
            self._brightness_widget.slider.setValue(brightness)
        self._brightness_widget.label.setText(f"Brightness: {brightness}")
        sbc.set_brightness(brightness, method=method)

    def _update_base_brightness_values(self):
        """Updates the background and screen brightness value.
        They will be passed to the BrightnessCalculator to calculate modified brightness.
        """
        _, background_image = self.cam.read()
        # threshold is the brightness value of the background.
        self._threshold = BrightnessCalculator.get_brightness_percentage(background_image)
        # base value is the current slider value, users can adjust it by themselves.
        self._base_value = self._brightness_widget.slider.value()

    def _stop_warning(self):
        """Set warning flag to False, so the warning dialog won't pop out again."""
        self._warning_flag = False

    def _close_dialog(self):
        """Close the warning dialog."""
        self._warning_widget.hide()
        self._set_brightness(80, set_slider=True)
        self._brightness_widget.slider.setEnabled(True)
        self._brightness_widget.checkbox.setEnabled(True)