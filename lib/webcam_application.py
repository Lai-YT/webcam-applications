from typing import Any, Dict, List

import cv2
import dlib
import imutils
import numpy
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from imutils import face_utils
from nptyping import Int, NDArray

from lib.angle_calculator import AngleCalculator, draw_landmarks_used_by_angle_calculator
from lib.distance_calculator import DistanceCalculator, draw_landmarks_used_by_distance_calculator
from lib.guard import DistanceSentinel, PostureChecker, TimeSentinel, mark_face
from lib.timer import Timer
from lib.train import ModelPath, ModelTrainer
from lib.image_type import ColorImage
from lib.path import to_abs_path

# This is the Model part, it knows nothing about View.
# One can pass options and parameters through View and Controller
# or directly call it with client code.
class WebcamApplication(QObject):

    # Signals used to communicate with controller.
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

        self._create_face_detectors()

    def enable_distance_measure(self, enable: bool, distance: float, warn_dist: float) -> None:
        """Note that if enable is False, other parameters are ignored."""
        self._distance_measure = enable
        if enable:
            self._create_distance_sentinel(distance, warn_dist)

    def enable_focus_time(self, enable: bool, time_limit: int, break_time: int) -> None:
        """Note that if enable is False, other parameters are ignored."""
        self._focus_time = enable
        if enable:
            self._create_time_sentinel(time_limit, break_time)

    def enable_posture_detect(self, enable: bool, model_path: ModelPath, warn_angle: float) -> None:
        """Note that if enable is False, other parameters are ignored."""
        self._posture_detect = enable
        if enable:
            self._create_posture_checker(model_path, warn_angle)

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
            self._timer = Timer()
            self._timer.start()

        webcam = cv2.VideoCapture(0)

        self.s_started.emit()

        while self._f_ready:
            _, frame = webcam.read()
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
                self._posture_checker.check_posture(canvas, frame, landmarks)
                draw_landmarks_used_by_angle_calculator(canvas, landmarks)
            if self._focus_time:
                # If the landmarks of face are clear, ths user is considered not focusing
                # on the screen, so the timer is paused.
                if not landmarks.any():
                    self._timer.pause()
                else:
                    self._timer.start()
                self._time_sentinel.break_time_if_too_long(self._timer)

            # zoom in the canvas (keep the ratio)
            canvas = imutils.resize(canvas, width=960)
            cv2.imshow("Webcam application", canvas)
            cv2.waitKey(refresh)
        # Release resources.
        webcam.release()
        cv2.destroyAllWindows()
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

    def _create_distance_sentinel(self, distance: float, warn_dist: float) -> None:
        # Creates the DistanceCalculator with reference image.
        ref_img: ColorImage = cv2.imread(to_abs_path("../img/ref_img.jpg"))
        faces: dlib.rectangles = self._face_detector(ref_img)
        if len(faces) != 1:
            # must have exactly one face in the reference image
            raise ValueError("should have exactly 1 face in the reference image")
        landmarks: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(self._shape_predictor(ref_img, faces[0]))
        self._distance_sentinel = DistanceSentinel(
            DistanceCalculator(landmarks, distance), warn_dist)

    def _create_posture_checker(self, model_path: ModelPath, warn_angle: float) -> None:
        self._posture_checker = PostureChecker(
            ModelTrainer.load_model(model_path), AngleCalculator(), warn_angle)

    def _create_time_sentinel(self, time_limit: int, break_time: int) -> None:
        self._time_sentinel = TimeSentinel(time_limit, break_time)
        self._time_sentinel.show()
        self.s_stopped.connect(self._time_sentinel.close_timer_widget)
