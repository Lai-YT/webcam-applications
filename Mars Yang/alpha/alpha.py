import argparse
import cv2
from typing import Any, Dict, List

import lib.app_visual as vs
from lib.face_distance_detector import DistanceDetector, FaceDetector
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from lib.train import *
from path import to_abs_path


"""parameters set by the user"""
ref_image_path: str = to_abs_path("img/ref_img.jpg")
model_path: str = to_abs_path("trained_model/posture_detection_model.h5")
params: List[float] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(float(line.rstrip("\n").split()[-1]))
face_dist_in_ref: float = params[0]
real_face_width:  float = params[1]


def do_applications(*, dist_measure: bool, focus_time: bool, post_watch: bool) -> None:
    """Enable the applications that are marked True."""
    webcam = cv2.VideoCapture(0)

    # commons
    if dist_measure or post_watch or focus_time:
        face_detector = FaceDetector()
    if post_watch or focus_time:
        gaze = GazeTracking()

    if dist_measure:
        distance_detector = DistanceDetector(
            cv2.imread(ref_image_path), face_dist_in_ref, real_face_width)
    if post_watch:
        model = model_path
    if focus_time:
        timer = Timer()
        timer.start()

    while webcam.isOpened():
        _, frame = webcam.read()
        frame = cv2.flip(frame, flipCode=1)  # mirrors, so horizontally flip

        # commons
        if dist_measure or post_watch or focus_time:
            face_detector.refresh(frame)
            frame = face_detector.mark_face()
        if post_watch or focus_time:
            gaze.refresh(frame)
            frame = gaze.mark_pupils()

        if dist_measure:
            distance_detector.estimate(frame)
            frame = vs.do_distance_measurement(frame, distance_detector)
        if post_watch:
            frame = vs.do_posture_watch(frame, model)
        if focus_time:
            frame = vs.do_focus_time_record(frame, timer, face_detector, gaze)

        cv2.imshow("alpha", frame)
        # ESC
        if cv2.waitKey(1) == 27:
            break
    else:
        raise IOError('Cannot open webcam')

    webcam.release()
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
