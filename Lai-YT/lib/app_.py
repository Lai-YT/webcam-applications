from typing import Any, Dict, List, Optional

import cv2
import dlib
import numpy
from PyQt5.QtGui import QImage
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from imutils import face_utils
from nptyping import Int, NDArray

from lib.angle_calculator import AngleCalculator, draw_landmarks_used_by_angle_calculator
from lib.distance_calculator import DistanceCalculator, draw_landmarks_used_by_distance_calculator
from lib.guard import DistanceSentinel, PostureChecker, TimeSentinel, mark_face
from lib.image_convert import ndarray_to_qimage
from lib.timer import Timer
from lib.train import ModelPath, ModelTrainer, PostureLabel
from lib.image_type import ColorImage
from lib.path import to_abs_path


class WebcamApplication(QObject):

    # Signals used to communicate with controller.
    s_frame_refreshed = pyqtSignal(QImage)
    s_distance_refreshed = pyqtSignal(float)
    s_time_refreshed = pyqtSignal(int, str)
    s_posture_refreshed = pyqtSignal(PostureLabel, str)
    s_started = pyqtSignal()  # emits just before getting in to the while-loop of start()
    s_stopped = pyqtSignal()  # emits just before leaving start()

    def __init__(self):
        super().__init__()
        # applications
        self._distance_measure: bool = False
        self._focus_time: bool = False
        self._posture_detect: bool = False

        # Used to break the capturing loop inside start().
        # If the application is in progress, sets the ready flag to False will stop it.
        self._f_ready: bool = False

        self._webcam = cv2.VideoCapture(0)
        self._create_face_detectors()
        self._create_guards()

    def set_distance_measure(
            self, *,
            enabled: Optional[bool] = None,
            camera_dist: Optional[float] = None,
            warn_dist: Optional[float] = None,
            warning_enabled: Optional[bool] = None) -> None:
        if camera_dist is not None:
            self._distance_sentinel.set_distance_calculator(DistanceCalculator(self._landmarks, camera_dist))
        if warn_dist is not None:
            self._distance_sentinel.set_warn_dist(warn_dist)
        if warning_enabled is not None:
            self._distance_sentinel.set_warning_enabled(warning_enabled)
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
            self._time_sentinel.set_time_limit(time_limit)
        if break_time is not None:
            self._time_sentinel.set_break_time(break_time)
        if warning_enabled is not None:
            self._time_sentinel.set_warning_enabled(warning_enabled)
        # Notice that enabled after all other arguments are set to prevent from AttributeError.
        if enabled is not None:
            self._time_sentinel.reset()
            self._focus_time = enabled
            if enabled:
                self._timer = Timer()  # Use a new timer.
                self._time_sentinel.show()
            else:
                self._time_sentinel.hide()

    def set_posture_detect(
            self, *,
            enabled: Optional[bool] = None,
            model_path: Optional[ModelPath] = None,
            warn_angle: Optional[float] = None,
            warning_enabled: Optional[bool] = None) -> None:
        if model_path is not None:
            self._posture_checker.set_model(ModelTrainer.load_model(model_path))
        if warn_angle is not None:
            self._posture_checker.set_warn_angle(warn_angle)
        if warning_enabled is not None:
            self._posture_checker.set_warning_enabled(warning_enabled)
        # Notice that enabled after all other arguments are set to prevent from AttributeError.
        if enabled is not None:
            self._posture_detect = enabled

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
                    self._distance_sentinel.warn_if_too_close(canvas, landmarks)
            if self._posture_detect:
                draw_landmarks_used_by_angle_calculator(canvas, landmarks)
                self._posture_checker.check_posture(canvas, frame, landmarks)
            if self._focus_time:
                # If the landmarks of face are clear, ths user is considered not focusing
                # on the screen, so the timer is paused.
                if not landmarks.any():
                    self._timer.pause()
                else:
                    self._timer.start()
                self._time_sentinel.break_time_if_too_long(self._timer)

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
        """Returns the numpy array with all elements in 0 if there isn't exactly 1 face in the frame.
        Note that one can use .any() to check if any of the elements is not 0.
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
        """Creates face detector and shape predictor for further use."""
        self._face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()
        self._shape_predictor = dlib.shape_predictor(to_abs_path("trained_models/shape_predictor_68_face_landmarks.dat"))

    def _create_guards(self):
        # Creates the DistanceCalculator with reference image.
        ref_img: ColorImage = cv2.imread(to_abs_path("../img/ref_img.jpg"))
        faces: dlib.rectangles = self._face_detector(ref_img)
        if len(faces) != 1:
            # must have exactly one face in the reference image
            raise ValueError("should have exactly 1 face in the reference image")
        self._landmarks: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(self._shape_predictor(ref_img, faces[0]))
        self._distance_sentinel = DistanceSentinel()
        self._distance_sentinel.s_distance_refreshed.connect(self.s_distance_refreshed)

        self._angle_calculator = AngleCalculator()
        self._posture_checker = PostureChecker(angle_calculator=self._angle_calculator)
        self._posture_checker.s_posture_refreshed.connect(self.s_posture_refreshed)

        self._time_sentinel = TimeSentinel()
        self._time_sentinel.s_time_refreshed.connect(self.s_time_refreshed)
        self.s_stopped.connect(self._time_sentinel.close_timer_widget)
