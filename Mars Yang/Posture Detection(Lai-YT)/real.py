import argparse
import cv2
from typing import List

import lib.app as app
from lib.face_distance_detector import FaceDistanceDetector
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from path import to_abs_path


"""parameters set by the user"""
ref_image_path: str = to_abs_path("img/ref_img.jpg")
params: List[float] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(float(line.rstrip('\n').split()[-1]))
face_to_cam_dist_in_ref: float = params[0]
personal_face_width: float = params[1]
warn_dist: float = params[2]


def do_applications(*, dist_measure: bool, focus_time: bool, post_watch: bool) -> None:
    """Enable the applications that are marked True."""
    # Initializations
    webcam = cv2.VideoCapture(0)

    if dist_measure or focus_time:
        face_distance_detector = FaceDistanceDetector(
            cv2.imread(ref_image_path), face_to_cam_dist_in_ref, personal_face_width)
    if post_watch:
        model = app.load_posture_model()
    if focus_time:
        gaze = GazeTracking()
        timer = Timer()
        timer.start()
    # Do
    while webcam.isOpened():
        _, frame = webcam.read()

        if dist_measure:
            face_distance_detector.estimate(frame)
            app.warn_if_too_close(face_distance_detector, warn_dist)
        if focus_time:
            # need face detection
            if not dist_measure:
                face_distance_detector.estimate(frame)
            # We send this frame to GazeTracking to analyze it
            gaze.refresh(frame)
            app.update_time(timer, face_distance_detector, gaze)
        if post_watch:
            app.watch_posture(frame, model)
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
    parser = argparse.ArgumentParser(description='webcam applications with distance measurement, eye focus timing and posture watching')
    parser.add_argument('-d', '--distance', help='enable distance measurement', action='store_true')
    parser.add_argument('-t', '--time', help='enable eye focus timing', action='store_true')
    parser.add_argument('-p', '--posture', help='enable posture watching', action='store_true')
    args = parser.parse_args()

    # if any of the arguments is True
    if any([value for key, value in vars(args).items()]):
        do_applications(dist_measure=args.distance, focus_time=args.time, post_watch=args.posture)
    else:
        parser.print_help()
