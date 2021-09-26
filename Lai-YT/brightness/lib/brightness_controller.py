import cv2
import screen_brightness_control as sbc
from PyQt5.QtCore import QObject, QThread, Qt, pyqtSignal, pyqtSlot

from lib.brightness_calculator import BrightnessCalculator
from lib.brightness_window import BrightnessGui
from lib.task_worker import TaskWorker


method = "wmi"
class BrightnessController(QObject):
    # Emits when the `Exit` button is clicked.
    s_exit = pyqtSignal()

    def __init__(self, gui: BrightnessGui):
        super().__init__()

        self._gui = gui

        # Since there are multiple fuctions that need to access camera,
        # make it an attribute instead of opening in a certain method.
        self._cam = cv2.VideoCapture(0)
        self._f_exit = False

        self._connect_signals()

        # Init the slider and label status to be as same as the user's screen brightness.
        self._set_brightness(sbc.get_brightness(method=method), set_slider=True)
        # Note that if remove this call, AttributeError might be raise at the
        # first time the checkbox is checked. This might be due to racing between
        # stateChanged and get_brightness_percentage. If the latter goes first,
        # self._threshold isn't defined yet.
        self._update_base_brightness_values()

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
        # Connect the siganls among widgets.
        self._gui.buttons["Exit"].clicked.connect(self._click_exit)
        # To have all resources release correctly,
        # make clicking `X` works as same as `Exit`.
        self._gui.set_clean_up_before_destroy(self._click_exit)
        # Notice that fast swithing between checked and unchecked may cause the
        # camera to shut down since camera.read takes time.
        self._gui.checkbox.stateChanged.connect(self._update_brightness_and_slider_visibility)
        # Label and screen should be set when the user adjust the slider.
        self._gui.slider.valueChanged.connect(
            lambda: self._set_brightness(self._gui.slider.value(), set_slider=False))
        # Connect the exit signal.
        self.s_exit.connect(self._gui.close)

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
            self._gui.slider.hide()
        else:
            self._set_brightness(sbc.get_brightness(method=method), set_slider=True)
            self._gui.slider.show()

    def _set_brightness(self, brightness: int, set_slider: bool):
        """Adjust the brightness of the screen manually or automatically.

        Arguments:
            brightness (int): The brightness value to set to the screen
            set_slider (bool): The value of slider will also be set is True
        """
        if set_slider:
            self._gui.slider.setValue(brightness)
        self._gui.label.setText(f"Brightness: {brightness}")
        sbc.set_brightness(brightness, method=method)

    def _update_base_brightness_values(self):
        """Updates the base environment and screen brightness value.
        They will be passed to the BrightnessCalculator to calculate modified brightness.
        """
        _, environment_image = self._cam.read()
        # threshold is the brightness value of the environment.
        self._threshold = BrightnessCalculator.get_brightness_percentage(environment_image)
        # base value is the brightness value of the screen under such environment,
        # which is the current slider value.
        self._base_value = self._gui.slider.value()

    def _capture_image(self):
        """Capture images and adjust the brightness instantly."""
        while not self._f_exit:
            _, frame = self._cam.read()

            # If "Brightness Optimization" is checked, adjust the brightness automatically.
            if self._gui.checkbox.isChecked():
                brightness = BrightnessCalculator.calculate_proper_screen_brightness(self._threshold, self._base_value, frame)
                # The value of the slider is kept unchanged, only the label and
                # the brightness of screen is adjusted.
                # This is because the slider is only used to change the base value,
                # which should be adjusted by the user.
                self._set_brightness(brightness, set_slider=False)

            cv2.waitKey(25)
        # Release the resources.
        self._cam.release()
        self.s_exit.emit()

    @pyqtSlot()
    def _click_exit(self):
        """Set exit flag to True."""
        self._f_exit = True
