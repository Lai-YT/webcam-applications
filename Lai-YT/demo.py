import argparse
import cv2
import dlib
from typing import Any, Dict, List

import lib.app as app
from lib.angle_calculator import AngleCalculator
from lib.distance_calculator import DistanceCalculator
from lib.timer import Timer
from lib.train import PostureMode, load_posture_model
from path import to_abs_path


"""parameters set by the user"""
params: List[str] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(line.rstrip('\n').split()[-1])

camera_dist = float(params[0])
face_width = float(params[1])
dist_limit = float(params[2])
time_limit = int(params[3])
break_time = int(params[4])


def do_applications(*, dist_measure: bool, focus_time: bool, post_watch: bool) -> None:
    """Enable the applications that are marked True."""
    # commons
    if dist_measure or post_watch or focus_time:
        face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()
        shape_predictor = dlib.shape_predictor(to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat'))

    if dist_measure:
        ref_img: ColorImage = cv2.imread(to_abs_path("img/ref_img.jpg"))
        face: dlib.rectangle = face_detector(ref_img)[0]
        shape: dlib.full_object_detection = shape_predictor(ref_img, face)
        distance_calculator = DistanceCalculator(shape, camera_dist, face_width)
    if post_watch:
        models: Dict[PostureMode, Any] = load_posture_model()
        angle_calculator = AngleCalculator()
    if focus_time:
        timer = Timer()
        timer.start()

    webcam = cv2.VideoCapture(0)
    while webcam.isOpened():
        _, frame = webcam.read()

        # commons
        if dist_measure or post_watch or focus_time:
            faces: dlib.rectangles = face_detector(frame)
            # doesn't handle multiple face
            if len(faces) > 1:
                raise
            if len(faces):
                shape = shape_predictor(frame, faces[0])

        if dist_measure and len(faces):
            app.warn_if_too_close(distance_calculator.calculate(shape), dist_limit)
        if post_watch:
            if len(faces):
                app.warn_if_angle_exceeds_threshold(angle_calculator.calculate(shape), 10.0)
            else:
                app.warn_if_slumped(frame, models[PostureMode.write])
        if focus_time:
            if not len(faces):
                timer.pause()
            else:
                timer.start()
            app.update_time_window(timer.time())
            app.break_time_if_too_long(timer, time_limit, break_time, webcam)
        # ESC
        if cv2.waitKey(1) == 27:
            break
    else:
        raise IOError('Cannot open webcam')

    # Releases
    webcam.release()
    if focus_time:
        timer.reset()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Webcam applications with distance measurement, eye focus timing and posture watching. Press "esc" to end the program.')
    parser.add_argument('-d', '--distance', help='warning shows if the user gets too close to the screen', action='store_true')
    parser.add_argument('-t', '--time', help='reminds when it\'s time to take a break', action='store_true')
    parser.add_argument('-p', '--posture', help='sound plays when the user has bad posture', action='store_true')
    args = parser.parse_args()

    # if any of the arguments is True
    if any([value for key, value in vars(args).items()]):
        do_applications(dist_measure=args.distance, focus_time=args.time, post_watch=args.posture)
    else:
        parser.print_help()
