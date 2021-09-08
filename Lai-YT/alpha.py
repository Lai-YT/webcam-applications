from typing import Any, Dict, List

import cv2
import dlib
import imutils
import numpy
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from imutils import face_utils
from nptyping import Int, NDArray
from tensorflow.keras import models

import lib.app_visual as vs
from lib.angle_calculator import AngleCalculator, draw_landmarks_used_by_angle_calculator
from lib.distance_calculator import DistanceCalculator, draw_landmarks_used_by_distance_calculator
from lib.timer import Timer
from lib.train import MODEL_PATH
from lib.image_type import ColorImage
from path import to_abs_path


# This is the Model part, it knows nothing about View.
# One can pass options and parameters through View and Controller
# or directly call it with client code.
class WebcamApplication(QObject):

    """Signals used to communicate with controller."""
    s_started = pyqtSignal()  # emits just before getting in to the while-loop of start()
    s_stopped = pyqtSignal()  # emits just before leaving start()

    def __init__(self):
        super().__init__()
        # settings
        self._distance_measure: bool = False
        self._face_width: float = 0  # Width of the user's face.
        self._distance: float = 0    # Distance between face and camera.
        self._warn_dist: float = 0

        self._focus_time: bool = False
        self._time_limit: int = 0
        self._break_time: int = 0

        self._posture_detect: bool = False
        self._warn_angle: float = 0
        # Used to break the capturing loop inside start().
        # If the application is in progress, sets the ready flag to False will stop it.
        # Note that it seems to be unable to call a setter method from another
        # thread to change the flag during the loop. Simply work around by a public flag.
        self.ready: bool = False

    @pyqtSlot()
    @pyqtSlot(int)
    def start(self, refresh: int = 1) -> None:
        """Starts the application.

        Arguments:
            refresh (int): Refresh speed in millisecond. 1ms in default.
        """
        # Set the flag to True so can start capturing.
        # Loop breaks if someone call close() and sets the flag to False.
        self.ready = True
        # Setup the objects we need for the corresponding application.
        self._setup_face_detectors()
        if self._distance_measure:
            self._setup_distance_measure()
        if self._posture_detect:
            self._setup_posture_detect()
        if self._focus_time:
            self._setup_focus_time()

        webcam = cv2.VideoCapture(0)

        self.s_started.emit()

        while self.ready:
            _, frame = webcam.read()
            # mirrors, so horizontally flip
            frame = cv2.flip(frame, flipCode=1)
            # separate detections and markings
            canvas: ColorImage = frame.copy()
            # Analyze the frame to get face landmarks.
            landmarks = self._get_landmarks(frame, canvas)
            # Do applications!
            if self._distance_measure:
                self._run_distance_measure(landmarks, canvas)
            if self._posture_detect:
                self._run_posture_detect(frame, landmarks, canvas)
            if self._focus_time:
                self._run_focus_time(landmarks, canvas)

            # zoom in the canvas (keep the ratio)
            canvas = imutils.resize(canvas, width=960)
            cv2.imshow("Webcam application", canvas)
            cv2.waitKey(refresh)
        # Release resources.
        webcam.release()
        cv2.destroyAllWindows()
        self.s_stopped.emit()

    def enable_distance_measure(self, enable: bool, face_width: float, distance: float, warn_dist: float) -> None:
        self._distance_measure = enable
        self._face_width = face_width
        self._distance = distance
        self._warn_dist = warn_dist

    def enable_focus_time(self, enable: bool, time_limit: int, break_time: int) -> None:
        self._focus_time = enable
        self._time_limit = time_limit
        self._break_time = break_time

    def enable_posture_detect(self, enable: bool, warn_angle: float) -> None:
        self._posture_detect = enable
        self._warn_angle = warn_angle

    def _setup_face_detectors(self) -> None:
        """Creates face detector and shape predictor for further use."""
        self._face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()
        self._shape_predictor = dlib.shape_predictor(to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat'))

    def _setup_distance_measure(self) -> None:
        """Creates the DistanceCalculator with reference image."""
        ref_img: ColorImage = cv2.imread(to_abs_path("img/ref_img.jpg"))
        faces: dlib.rectangles = self._face_detector(ref_img)
        if len(faces) != 1:
            # must have exactly one face in the reference image
            raise ValueError("should have exactly 1 face in the reference image")
        landmarks: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(self._shape_predictor(ref_img, faces[0]))
        self._distance_calculator = DistanceCalculator(landmarks, self._distance, self._face_width)

    def _setup_posture_detect(self) -> None:
        """Loads model and Creates AngleCalculator."""
        self._model = models.load_model(MODEL_PATH)
        self._angle_calculator = AngleCalculator()

    def _setup_focus_time(self) -> None:
        """Creates a Timer and start timing."""
        self._timer = Timer()
        self._timer.start()

    def _get_landmarks(self, frame: ColorImage, canvas: ColorImage) -> NDArray[(68, 2), Int[32]]:
        """Returns the numpy array with all elements in 0 if there isn't exactly 1 face in the frame.
        Note that one can use .any() to check if any of the elements is not 0.
        """
        faces: dlib.rectangles = self._face_detector(frame)
        # doesn't handle multiple faces
        if len(faces) == 1:
            landmarks: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(self._shape_predictor(frame, faces[0]))
            vs.mark_face(canvas, face_utils.rect_to_bb(faces[0]), landmarks)
            draw_landmarks_used_by_distance_calculator(canvas, landmarks)
        else:
            landmarks = numpy.zeros(shape=(68, 2), dtype=numpy.int32)
        return landmarks

    def _run_distance_measure(self, landmarks: NDArray[(68, 2), Int[32]], canvas: ColorImage) -> None:
        if landmarks.any():
            vs.put_distance_text(canvas, self._distance_calculator.calculate(landmarks))
            vs.warn_if_too_close(canvas, self._distance_calculator.distance(), self._warn_dist)

    def _run_posture_detect(self, frame: ColorImage, landmarks: NDArray[(68, 2), Int[32]], canvas: ColorImage) -> None:
        # If the landmarks of face are clear, use AngleCalculator to calculate the slope
        # precisely; otherwise use the model to predict the posture.
        if landmarks.any():
            vs.do_posture_angle_check(canvas, self._angle_calculator.calculate(landmarks), self._warn_angle)
            draw_landmarks_used_by_angle_calculator(canvas, landmarks)
        else:
            vs.do_posture_model_predict(frame, self._model, canvas)

    def _run_focus_time(self, landmarks: NDArray[(68, 2), Int[32]], canvas: ColorImage) -> None:
        # If the landmarks of face are clear, ths user is considered not focusing
        # on the screen, so the timer is paused.
        if not landmarks.any():
            self._timer.pause()
        else:
            self._timer.start()
        # Time is paused at break, so check first.
        vs.break_time_if_too_long(canvas, self._timer, self._time_limit, self._break_time)
        vs.record_focus_time(canvas, self._timer.time(), self._timer.is_paused())
