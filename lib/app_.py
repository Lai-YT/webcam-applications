from typing import Any, Dict, List, Optional

import cv2
import dlib
import numpy
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from imutils import face_utils
from nptyping import Int, NDArray

from gui.popup_widget import TimeState
from lib.angle_calculator import AngleCalculator, draw_landmarks_used_by_angle_calculator
from lib.brightness_calcuator import BrightnessMode
from lib.brightness_controller import BrightnessController
from lib.distance_calculator import DistanceCalculator, draw_landmarks_used_by_distance_calculator
from lib.guard import DistanceGuard, PostureGuard, TimeGuard, TextColor, global_grader_for_guards, mark_face
from lib.image_convert import ndarray_to_qimage
from lib.timer import Timer
from lib.train import ModelPath, ModelTrainer, PostureLabel
from lib.image_type import ColorImage
from lib.path import to_abs_path


class WebcamApplication(QObject):
    """
    The WebcamApplication provides 4 main applications:
        distance measurement,
        focus timing,
        posture detection,
        brightness optimization

    Signals:
        s_distance_refreshed:
            Emits everytime distance measurement has a new result.
            Sends the new distance.
        s_time_refreshed:
            Emits everytime the timer is updated.
            Sends the time and its state.
        s_posture_refreshed:
            Emits everytime posture detection has a new result.
            Sends the label of posture and few explanations.
        s_brightness_refreshed:
            Emits everytime the brightness of screen is updated.
            Sends the new brightness value.
        s_grade_refreshed:
            Emits everytime a new grade is published.
            Sends the new concentration grade.
        s_frame_refreshed:
            Emits every time a new frame is captured.
            Sends the new frame.
        s_started:
            Emits after the WebcamApplication starts running.
        s_stopped:
            Emits after the WebcamApplication stops running.
    """

    # Signals used to communicate with controller.
    s_frame_refreshed = pyqtSignal(QImage)
    s_distance_refreshed = pyqtSignal(float, TextColor)
    s_time_refreshed = pyqtSignal(int, TimeState)
    s_posture_refreshed = pyqtSignal(PostureLabel, str, TextColor)
    s_brightness_refreshed = pyqtSignal(int)
    s_grade_refreshed = pyqtSignal(float)
    s_started = pyqtSignal()  # emits just before getting in to the while-loop of start()
    s_stopped = pyqtSignal()  # emits just before leaving start()

    def __init__(self):
        super().__init__()
        # applications
        self._distance_measure: bool = False
        self._focus_time: bool = False
        self._posture_detect: bool = False
        self._brightness_optimize: bool = False

        # Used to break the capturing loop inside start().
        # If the application is in progress, sets the ready flag to False will stop it.
        self._f_ready: bool = False

        self._webcam = cv2.VideoCapture(0)
        self._create_face_detectors()
        self._create_brightness_controller()
        self._create_guards()
        self._connect_concentration_grader()

    def set_distance_measure(
            self, *,
            enabled: Optional[bool] = None,
            camera_dist: Optional[float] = None,
            warn_dist: Optional[float] = None,
            warning_enabled: Optional[bool] = None) -> None:
        if camera_dist is not None:
            self._distance_guard.set_distance_calculator(DistanceCalculator(self._landmarks, camera_dist))
        if warn_dist is not None:
            self._distance_guard.set_warn_dist(warn_dist)
        if warning_enabled is not None:
            self._distance_guard.set_warning_enabled(warning_enabled)
        # Notice that enabled after all other arguments are set to prevent from AttributeError.
        if enabled is not None:
            self._distance_measure = enabled

    def set_focus_time(
            self, *,
            enabled: Optional[bool] = None,
            time_limit: Optional[int] = None,
            break_time: Optional[int] = None,
            warning_enabled: Optional[bool] = None) -> None:
        if time_limit is not None:
            self._time_guard.set_time_limit(time_limit)
        if break_time is not None:
            self._time_guard.set_break_time(break_time)
        if warning_enabled is not None:
            self._time_guard.set_warning_enabled(warning_enabled)
        # Notice that enabled after all other arguments are set to prevent from AttributeError.
        if enabled is not None:
            self._time_guard.reset()
            self._focus_time = enabled
            if enabled:
                self._timer = Timer()  # Use a new timer.
                self._time_guard.show()
            else:
                self._time_guard.hide()

    def set_posture_detect(
            self, *,
            enabled: Optional[bool] = None,
            model_path: Optional[ModelPath] = None,
            warn_angle: Optional[float] = None,
            warning_enabled: Optional[bool] = None) -> None:
        if model_path is not None:
            self._posture_guard.set_model(ModelTrainer.load_model(model_path))
        if warn_angle is not None:
            self._posture_guard.set_warn_angle(warn_angle)
        if warning_enabled is not None:
            self._posture_guard.set_warning_enabled(warning_enabled)
        # Notice that enabled after all other arguments are set to prevent from AttributeError.
        if enabled is not None:
            self._posture_detect = enabled

    def set_brightness_optimization(
            self, *,
            enabled: Optional[bool] = None,
            slider_value: Optional[int] = None,
            webcam_enabled: Optional[bool] = None,
            color_system_enabled: Optional[bool] = None) -> None:
        if slider_value is not None:
            self._brightness_controller.set_base_value(slider_value)
        if webcam_enabled is not None:
            self._brightness_modes_enabled[BrightnessMode.WEBCAM] = webcam_enabled
        if color_system_enabled is not None:
            self._brightness_modes_enabled[BrightnessMode.COLOR_SYSTEM] = color_system_enabled
        # If any of the enabled is changed, reset the mode.
        if webcam_enabled or color_system_enabled:
            if all(self._brightness_modes_enabled.values()):
                self._brightness_controller.set_mode(BrightnessMode.BOTH)
            elif self._brightness_modes_enabled[BrightnessMode.WEBCAM]:
                self._brightness_controller.set_mode(BrightnessMode.WEBCAM)
            elif self._brightness_modes_enabled[BrightnessMode.COLOR_SYSTEM]:
                self._brightness_controller.set_mode(BrightnessMode.COLOR_SYSTEM)
        # Notice that enabled after all other arguments are set to prevent from AttributeError.
        if enabled is not None:
            self._brightness_optimize = enabled

    @pyqtSlot()
    @pyqtSlot(int)
    def start(self, refresh: int = 1) -> None:
        """Starts the applications that has been enabled.

        Arguments:
            refresh (int): Refresh speed in millisecond. 1ms in default.
        """
        # Set the flag to True so can start capturing.
        # Loop breaks if someone calls stop() and sets the flag to False.
        self._f_ready = True

        # focus time needs a timer to help.
        if self._focus_time:
            self._timer.start()

        self.s_started.emit()

        while self._f_ready:
            _, frame = self._webcam.read()
            # mirrors, so horizontally flip
            frame = cv2.flip(frame, flipCode=1)
            # separate detections and markings
            canvas: ColorImage = frame.copy()
            # Analyze the frame to get face landmarks.
            landmarks: NDArray[(68, 2), Int[32]] = self._get_landmarks(canvas, frame)
            # Do applications!
            if self._distance_measure:
                if landmarks.any():
                    self._distance_guard.warn_if_too_close(canvas, landmarks)
            if self._posture_detect:
                draw_landmarks_used_by_angle_calculator(canvas, landmarks)
                self._posture_guard.check_posture(canvas, frame, landmarks)
            if self._focus_time:
                # If the landmarks of face are clear, ths user is considered not focusing
                # on the screen, so the timer is paused.
                if not landmarks.any():
                    self._timer.pause()
                else:
                    self._timer.start()
                self._time_guard.break_time_if_too_long(self._timer)
            if self._brightness_optimize:
                # pass canvas if webcam is checked
                if self._brightness_modes_enabled[BrightnessMode.WEBCAM]:
                    self._brightness_controller.set_webcam_frame(canvas)
                if self._brightness_modes_enabled[BrightnessMode.COLOR_SYSTEM]:
                    self._brightness_controller.refresh_color_system_screenshot()
                self._brightness_controller.optimize_brightness()

            self.s_frame_refreshed.emit(ndarray_to_qimage(canvas))
            cv2.waitKey(refresh)
        # Release resources.
        self._webcam.release()
        self.s_stopped.emit()

    @pyqtSlot()
    def stop(self) -> None:
        """Stops the execution loop by changing the flag."""
        self._f_ready = False

    def _get_landmarks(self, canvas: ColorImage, frame: ColorImage) -> NDArray[(68, 2), Int[32]]:
        """Returns the numpy array with all elements in 0 if there isn't exactly
        1 face in the frame.

        Note that one can use .any() to check if any of the elements is not 0.

        Arguments:
            canvas: The image to draw the landmarks on.
            frame: The image to get landmarks of.
        """
        faces: dlib.rectangles = self._face_detector(frame)
        # doesn't handle multiple faces
        if len(faces) == 1:
            landmarks: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(self._shape_predictor(frame, faces[0]))
            mark_face(canvas, face_utils.rect_to_bb(faces[0]), landmarks)
            draw_landmarks_used_by_distance_calculator(canvas, landmarks)
        else:
            landmarks = numpy.zeros(shape=(68, 2), dtype=numpy.int32)
        return landmarks

    def _create_face_detectors(self) -> None:
        """Creates face detector and shape predictor."""
        self._face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()
        self._shape_predictor = dlib.shape_predictor(to_abs_path("trained_models/shape_predictor_68_face_landmarks.dat"))

    def _create_brightness_controller(self):
        """Creates brightness calculator and connects its signals."""
        self._brightness_controller = BrightnessController()
        self._brightness_controller.s_brightness_refreshed.connect(self.s_brightness_refreshed)
        # This dict records whether the modes have been enabled.
        # So when both modes are True, we know a BOTH mode should be set.
        self._brightness_modes_enabled: Dict[BrightnessMode, bool] = {
            BrightnessMode.WEBCAM: False,
            BrightnessMode.COLOR_SYSTEM: False,
        }

    def _create_guards(self):
        """Creates guards used in WebcamApplication and connects their signals."""
        # Creates the DistanceCalculator with reference image.
        ref_img: ColorImage = cv2.imread(to_abs_path("../img/ref_img.jpg"))
        faces: dlib.rectangles = self._face_detector(ref_img)
        if len(faces) != 1:
            # must have exactly one face in the reference image
            raise ValueError("should have exactly 1 face in the reference image")
        self._landmarks: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(self._shape_predictor(ref_img, faces[0]))
        self._distance_guard = DistanceGuard()
        self._distance_guard.s_distance_refreshed.connect(self.s_distance_refreshed)

        self._angle_calculator = AngleCalculator()
        self._posture_guard = PostureGuard(angle_calculator=self._angle_calculator)
        self._posture_guard.s_posture_refreshed.connect(self.s_posture_refreshed)

        self._time_guard = TimeGuard()
        self._time_guard.s_time_refreshed.connect(self.s_time_refreshed)
        self.s_stopped.connect(self._time_guard.close_timer_widget)

    def _connect_concentration_grader(self) -> None:
        """Connects signals of the ConcentrationGrader used by guards."""
        global_grader_for_guards.s_grade_refreshed.connect(self.s_grade_refreshed)
