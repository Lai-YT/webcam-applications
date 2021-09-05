import argparse
from typing import Any, Dict, List, Tuple

import cv2
import dlib
import numpy
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
from win32api import GetSystemMetrics


# This is the Model part, it knows nothing about View.
# One can pass options and parameters through View and Controller
# or directly call it with client code.
class WebcamApplication:
    def __init__(self):
        # settings
        self._distance_measure: bool = False
        self._face_width: float = 0  # Width of the user's face.
        self._distance: float = 0    # Distance between face and camera.
        self._focus_time: bool = False
        self._posture_detect: bool = False
        # flags
        self._ready: bool = False    # Used to break the capturing loop inside start()
        # window info
        self._window_size: Tuple = (960, 720) # Original size: (640, 480)
        self._window_x = (GetSystemMetrics(0) - self._window_size[0]) / 2 # centrally aligned position
        self._window_y = (GetSystemMetrics(1) - (self._window_size[1] + 40)) / 2
        # print(self._window_x, self._window_y) # (480, 160)

    def start(self, refresh: int = 1) -> None:
        """Starts the application.

        Arguments:
            refresh (int): Refresh speed in millisecond. 1ms in default.
        """
        # Set the flag to True so can start capturing.
        # Loop breaks if someone calsl close() and sets the flag to False.
        self._ready = True

        self._setup_face_detectors()
        if self._distance_measure:
            self._setup_distance_measure()
        if self._posture_detect:
            self._setup_posture_detect()
        if self._focus_time:
            self._setup_focus_time()

        webcam = cv2.VideoCapture(0)
        while self._ready:
            _, frame = webcam.read()
            # zoom in the frame
            frame = cv2.resize(frame, self._window_size, interpolation=cv2.INTER_AREA)
            # mirrors, so horizontally flip
            frame = cv2.flip(frame, flipCode=1)
            # separate detections and markings
            canvas: ColorImage = frame.copy()

            landmarks = self._get_landmarks(frame, canvas)
            if self._distance_measure:
                self._run_distance_measure(landmarks, canvas)
            if self._posture_detect:
                self._run_posture_detect(frame, landmarks, canvas)
            if self._focus_time:
                self._run_focus_time(landmarks, canvas)

            cv2.imshow("Webcam application", canvas)
            cv2.moveWindow("Webcam application", 480, 160)
            cv2.waitKey(refresh)
        # Release resources.
        webcam.release()
        cv2.destroyAllWindows()

    def close(self) -> None:
        """Sets the ready flag to False. So if the application is in progress, it'll be stopped."""
        self._ready = False

    def enable_distance_measure(self, enable: bool, face_width: float, distance: float) -> None:
        self._distance_measure = enable
        self._face_width = face_width
        self._distance = distance

    def enable_focus_time(self, enable: bool) -> None:
        self._focus_time = enable

    def enable_posture_detect(self, enable: bool) -> None:
        self._posture_detect = enable

    def _setup_face_detectors(self) -> None:
        self._face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()
        self._shape_predictor = dlib.shape_predictor(to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat'))

    def _setup_distance_measure(self) -> None:
        ref_img: ColorImage = cv2.imread(to_abs_path("img/ref_img.jpg"))
        faces: dlib.rectangles = self._face_detector(ref_img)
        if len(faces) != 1:
            # must have exactly one face in the reference image
            raise ValueError("should have exactly 1 face in the reference image")
        landmarks: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(self._shape_predictor(ref_img, faces[0]))
        self._distance_calculator = DistanceCalculator(landmarks, self._distance, self._face_width)

    def _setup_posture_detect(self) -> None:
        self._model = models.load_model(MODEL_PATH)
        self._angle_calculator = AngleCalculator()

    def _setup_focus_time(self) -> None:
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

    def _run_posture_detect(self, frame: ColorImage, landmarks: NDArray[(68, 2), Int[32]], canvas: ColorImage) -> None:
        if landmarks.any():
            vs.do_posture_angle_check(canvas, self._angle_calculator.calculate(landmarks), 10.0)
            draw_landmarks_used_by_angle_calculator(canvas, landmarks)
        else:
            vs.do_posture_model_predict(frame, self._model, canvas)

    def _run_focus_time(self, landmarks: NDArray[(68, 2), Int[32]], canvas: ColorImage) -> None:
        if not landmarks.any():
            self._timer.pause()
        else:
            self._timer.start()
        vs.record_focus_time(canvas, self._timer.time(), self._timer.is_paused())


if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication

    from gui.main_controller import GuiController
    from gui.main_window import ApplicationGui

    app = QApplication(sys.argv)
    # Create the plain GUI.
    app_gui = ApplicationGui()
    app_gui.show()
    # Take control of the GUI and the Application.
    controller = GuiController(app=WebcamApplication(), gui=app_gui)
    # Execute the event loop.
    sys.exit(app.exec())
