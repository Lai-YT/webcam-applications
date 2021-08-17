import argparse
import cv2
import dlib
from tensorflow.keras import models
from typing import Any, Dict, List

import lib.app_visual as vs
from lib.angle_calculator import AngleCalculator, draw_landmarks_used_by_angle_calculator
from lib.distance_calculator import DistanceCalculator, draw_landmarks_used_by_distance_calculator
from lib.timer import Timer
from lib.train import MODEL_PATH
from lib.video_writer import VideoWriter
from lib.image_type import ColorImage
from path import to_abs_path


"""parameters set by the user"""
params: List[float] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(float(line.rstrip("\n").split()[-1]))
camera_dist: float = params[0]
face_width:  float = params[1]

video_writer = VideoWriter(to_abs_path("output/video"), fps=7.0)

def do_applications(dist_measure: bool, focus_time: bool, post_watch: bool) -> None:
    """Enable the applications that are marked True."""
    webcam = cv2.VideoCapture(0)

    # commons
    if dist_measure or post_watch or focus_time:
        face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()
        shape_predictor = dlib.shape_predictor(to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat'))

    if dist_measure:
        ref_img: ColorImage = cv2.imread(to_abs_path("img/ref_img.jpg"))
        faces: dlib.rectangles = face_detector(ref_img)
        if len(faces) != 1:
            # must have exactly one face in the reference image
            raise ValueError("should have exactly 1 face in the reference image")
        shape: dlib.full_object_detection = shape_predictor(ref_img, faces[0])
        distance_calculator = DistanceCalculator(shape, camera_dist, face_width)
    if post_watch:
        model = models.load_model(MODEL_PATH)
        angle_calculator = AngleCalculator()
    if focus_time:
        timer = Timer()
        timer.start()

    while webcam.isOpened():
        _, frame = webcam.read()
        frame = cv2.flip(frame, flipCode=1)  # mirrors, so horizontally flip
        # separate detections and markings
        canvas: ColorImage = frame.copy()

        # commons
        if dist_measure or post_watch or focus_time:
            faces = face_detector(frame)
            # doesn't handle multiple faces
            if len(faces) > 1:
                continue
            if len(faces):
                has_face: bool = True
                shape = shape_predictor(frame, faces[0])
                canvas = vs.mark_face(canvas, faces[0], shape)
                canvas = draw_landmarks_used_by_distance_calculator(canvas, shape)
            else:
                has_face = False

        if dist_measure and has_face:
            canvas = vs.put_distance_text(canvas, distance_calculator.calculate(shape))
        if post_watch:
            if has_face:
                canvas = vs.do_posture_angle_check(canvas, angle_calculator.calculate(shape), 10.0)
                canvas = draw_landmarks_used_by_angle_calculator(canvas, shape)
            else:
                canvas = vs.do_posture_model_predict(frame, model, canvas)
        if focus_time:
            if not has_face:
                timer.pause()
            else:
                timer.start()
            canvas = vs.record_focus_time(canvas, timer.time(), timer.is_paused())

        video_writer.write(canvas)
        cv2.imshow("alpha", canvas)
        # ESC
        if cv2.waitKey(1) == 27:
            break
    else:
        raise IOError('Cannot open webcam')

    webcam.release()
    video_writer.release()
    if focus_time:
        timer.reset()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='visualized ver. of webcam applications with distance measurement, eye focus timing and posture watching')
    parser.add_argument('-d', '--distance', help='enable distance measurement', action='store_true')
    parser.add_argument('-t', '--time', help='enable eye focus timing', action='store_true')
    parser.add_argument('-p', '--posture', help='enable posture watching', action='store_true')
    args = parser.parse_args()

    # if any of the arguments is True
    if any([value for key, value in vars(args).items()]):
        do_applications(dist_measure=args.distance, focus_time=args.time, post_watch=args.posture)
    else:
        parser.print_help()
