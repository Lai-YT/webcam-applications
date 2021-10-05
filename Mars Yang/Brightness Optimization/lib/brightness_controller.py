import cv2
import numpy as np

import screen_brightness_control as sbc
from PyQt5 import QtWidgets
from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QApplication

from lib.brightness_calculator import BrightnessCalculator
from lib.brightness_widget import BrightnessWidget
from lib.component import DontShowAgainWarningMessage
from lib.task_worker import TaskWorker


method = "wmi"
class BrightnessController(QObject):
    # Emits when the `Exit` button is clicked.
    s_exit = pyqtSignal()
    enable_start_button = pyqtSignal()

    def __init__(self, mode: str):
        super().__init__()

        self._mode = mode
        self._create_widgets()

        # Since there are multiple fuctions that need to access camera,
        # make it an attribute instead of opening in a certain method.
        self._cam = cv2.VideoCapture(0)

        self._connect_signals()
        self._advance_preparation()

        if self._mode == "color-system":
            print("Sorry, this part is not prepared yet.")
        else:
            # The widget needs to be shown, otherwise it will run invisibly.
            self._widget.show()
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

    def _create_widgets(self):
        """Creates the widgets for controller to control."""
        self._widget = BrightnessWidget()

        self._warning_dialog = DontShowAgainWarningMessage(
            "High brightness may reduce CPU performance\n and harm you sight.",
            parent=self._widget)  # modal dialog blocks inputs to parents.

    def _connect_signals(self):
        self._widget.buttons["Exit"].clicked.connect(self.click_exit)
        # To have all resources release correctly,
        # make clicking 'X' works as same as 'Exit'.
        self._widget.set_clean_up_before_destroy(self.click_exit)
        # The slider has two states, depending on the action user takes.
        self._widget.checkbox.stateChanged.connect(self._update_brightness_and_slider_visibility)
        # Label and screen should be set when the user adjust the slider.
        self._widget.slider.valueChanged.connect(
            lambda: self._set_brightness(self._widget.slider.value(), set_slider=False))
        # Base brightness value is check after released.
        self._widget.slider.sliderReleased.connect(self._warn_if_too_bright)
        # Connect the exit signal.
        self.s_exit.connect(self._widget.close)

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
            self._widget.slider.hide()
        else:
            self._set_brightness(sbc.get_brightness(method=method), set_slider=True)
            self._widget.slider.show()

    def _advance_preparation(self):
        """Init the slider and label status to be as same as the user's screen brightness."""
        self._set_brightness(sbc.get_brightness(method=method), set_slider=True)
        # Note that if remove this call, AttributeError might be raise at the
        # first time the checkbox is checked. This might be due to racing between
        # stateChanged and get_brightness_percentage. If the latter goes first,
        # self._threshold isn't defined yet.
        self._update_base_brightness_values()

    def _capture_image(self):
        """Capture images and adjust the brightness instantly."""
        self._f_exit = False

        while not self._f_exit:
            _, frame = self._cam.read()
            frame = cv2.flip(frame, flipCode=1) # horizontally flip

            # If "Brightness Optimization" is checked, adjust the brightness automatically.
            if self._widget.checkbox.isChecked():
                self._optimize_brightness(frame)

            cv2.waitKey(25)

        # Close the webcam and emit the exit signal.
        self._cam.release()
        cv2.destroyAllWindows()
        self.s_exit.emit()

    # Note that this method is public to make main controller able to close the
    # BrightnessWidget.
    @pyqtSlot()
    def click_exit(self):
        """
        Set exit flag to True and emit a signal to main controller 
        to enable the start button.
        """
        self._f_exit = True
        self.enable_start_button.emit() 

    def _optimize_brightness(self, frame):
        """Control screen brightness automatically in two different modes."""
        # Screenshot and turn image type to np.array
        if self._mode == "color-system":
            screen = QtWidgets.QApplication.primaryScreen()
            # image type: pixmap
            image = screen.grabWindow(QApplication.desktop().winId())
            image = self._qpixmap_to_ndarray(image)

        brightness = BrightnessCalculator.calculate_proper_screen_brightness(
            self._mode, self._threshold, self._base_value, frame)
        # The value of the slider is kept unchanged, only the label and
        # the brightness of screen is adjusted.
        # This is because the slider is only used to change the base value,
        # which should be adjusted by the user.
        self._set_brightness(brightness, set_slider=False)

    @staticmethod
    def _qpixmap_to_ndarray(image: QPixmap) -> "NDarray[(Any, Any, 3), UInt8]":
        qimage = image.toImage()
    
        width = qimage.width()
        height = qimage.height()

        byte_str = qimage.constBits().asstring(height * width * 4)
        ndarray = np.frombuffer(byte_str, np.uint8).reshape((height, width, 4))

        return ndarray

    @pyqtSlot()
    def _warn_if_too_bright(self):
        # If screen brightness > 80, the warning dialog will pop out.
        if (self._widget.slider.value() > 80
                and not self._warning_dialog.dont_show_again_checkbox.isChecked()):
            self._warning_dialog.exec()

    def _set_brightness(self, brightness: int, set_slider: bool):
        """Adjust the brightness of the screen manually or automatically.

        Arguments:
            brightness (int): The brightness value to set to the screen
            set_slider (bool): The value of slider will also be set is True
        """
        if set_slider:
            self._widget.slider.setValue(brightness)
        self._widget.label.setText(f"Brightness: {brightness}")
        sbc.set_brightness(brightness, method=method)

    def _update_base_brightness_values(self):
        """Updates the background and screen brightness value.
        They will be passed to the BrightnessCalculator to calculate modified brightness.
        """
        _, background_image = self._cam.read()
        # threshold is the brightness value of the background.
        self._threshold = BrightnessCalculator.get_brightness_percentage(background_image)
        # base value is the current slider value, users can adjust it by themselves.
        self._base_value = self._widget.slider.value()
        # To reduce the camera resource access racing problem (the user click `start`
        # immediately after a sliderReleased), delay a short amount of time.
        cv2.waitKey(750)