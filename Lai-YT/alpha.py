import argparse
from typing import Any, Dict, List

import cv2
import dlib
from imutils import face_utils
from tensorflow.keras import models

import lib.app_visual as vs
from lib.angle_calculator import AngleCalculator, draw_landmarks_used_by_angle_calculator
from lib.distance_calculator import DistanceCalculator, draw_landmarks_used_by_distance_calculator
from lib.timer import Timer
from lib.train import MODEL_PATH
from lib.video_writer import VideoWriter
from lib.image_type import ColorImage
from path import to_abs_path


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

    def start(self) -> None:
        # Set the flag to True so can start capturing.
        # Loop breaks if someone calsl close() and sets the flag to False.
        self._ready = True
        # common initialization
        if self._distance_measure or self._posture_detect or self._focus_time:
            face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()
            shape_predictor = dlib.shape_predictor(to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat'))

        if self._distance_measure:
            ref_img: ColorImage = cv2.imread(to_abs_path("img/ref_img.jpg"))
            faces: dlib.rectangles = face_detector(ref_img)
            if len(faces) != 1:
                # must have exactly one face in the reference image
                raise ValueError("should have exactly 1 face in the reference image")
            landmarks: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(shape_predictor(ref_img, faces[0]))
            distance_calculator = DistanceCalculator(landmarks, self._distance, self._face_width)
        if self._posture_detect:
            model = models.load_model(MODEL_PATH)
            angle_calculator = AngleCalculator()
        if self._focus_time:
            timer = Timer()
            timer.start()

        video_writer = VideoWriter(to_abs_path("output/video"), fps=7.0)
        webcam = cv2.VideoCapture(0)

        while self._ready:
            _, frame = webcam.read()
            frame = cv2.flip(frame, flipCode=1)  # mirrors, so horizontally flip
            # separate detections and markings
            canvas: ColorImage = frame.copy()
            # commons
            if self._distance_measure or self._posture_detect or self._focus_time:
                faces = face_detector(frame)
                # doesn't handle multiple faces
                if len(faces) > 1:
                    continue
                if len(faces):
                    has_face: bool = True
                    landmarks = face_utils.shape_to_np(shape_predictor(frame, faces[0]))
                    canvas = vs.mark_face(canvas, face_utils.rect_to_bb(faces[0]), landmarks)
                    canvas = draw_landmarks_used_by_distance_calculator(canvas, landmarks)
                else:
                    has_face = False

            if self._distance_measure and has_face:
                canvas = vs.put_distance_text(canvas, distance_calculator.calculate(landmarks))
            if self._posture_detect:
                if has_face:
                    canvas = vs.do_posture_angle_check(canvas, angle_calculator.calculate(landmarks), 10.0)
                    canvas = draw_landmarks_used_by_angle_calculator(canvas, landmarks)
                else:
                    canvas = vs.do_posture_model_predict(frame, model, canvas)
            if self._focus_time:
                if not has_face:
                    timer.pause()
                else:
                    timer.start()
                canvas = vs.record_focus_time(canvas, timer.time(), timer.is_paused())
            # video_writer.write(canvas)
            cv2.imshow("Webcam application", canvas)
            cv2.waitKey(1)
        # Release resources.
        webcam.release()
        video_writer.release()
        cv2.destroyAllWindows()

    def close(self) -> None:
        """Sets the ready flag to False, so if the application is in progress, it'll be stopped."""
        self._ready = False

    def enable_distance_measure(self, enable, face_width, distance):
        self._distance_measure = enable
        self._face_width = face_width
        self._distance = distance

    def enable_focus_time(self, enable):
        self._focus_time = enable

    def enable_posture_detect(self, enable):
        self._posture_detect = enable


if __name__ == '__main__':
    import sys

    from PyQt5.QtWidgets import QApplication

    from gui.controller import GuiController
    from gui.view import ApplicationGui

    app = QApplication(sys.argv)
    # Create the plain GUI.
    app_gui = ApplicationGui()
    app_gui.show()
    # Take control of the GUI and the Application.
    controller = GuiController(model=WebcamApplication(), gui=app_gui)
    # Execute the event loop.
    sys.exit(app.exec())
