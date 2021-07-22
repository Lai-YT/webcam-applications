import argparse
import cv2
import numpy
from typing import List

from lib.application import *
from lib.face_distance_detector import FaceDistanceDetector
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from path import to_abs_path


"""parameters set by the user"""
ref_image_path: str = to_abs_path("img/ref_img.jpg")
params: List[float] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(float(line.rstrip("\n").split()[-1]))
face_to_cam_dist_in_ref: float = params[0]
personal_face_width:     float = params[1]

# UnicodeDecodeError occurs when I put in application.py,
# might due to broken path.
mp3file: str = to_abs_path("lib/sounds/what.mp3")


def do_applications(*, dist_measure: bool, focus_time: bool, post_watch: bool) -> None:
    webcam = cv2.VideoCapture(0)

    if dist_measure or focus_time:
        distance_detector = FaceDistanceDetector(
            cv2.imread(ref_image_path), face_to_cam_dist_in_ref, personal_face_width)
    if post_watch:
        model = load_posture_model()
    if focus_time:
        gaze = GazeTracking()
        timer = Timer()
        timer.start()

    while webcam.isOpened():
        _, frame = webcam.read()
        frame = cv2.flip(frame, flipCode=1)  # mirrors, so horizontally flip

        if dist_measure:
            frame = do_distance_measurement(frame, distance_detector)
        if focus_time:
            # Need face detection
            if not dist_measure:
                frame = do_distance_measurement(frame, distance_detector, face_only=True)
            frame = do_gaze_tracking(frame, gaze)
            frame = do_focus_time_record(frame, timer, distance_detector, gaze)
        if post_watch:
            frame = do_posture_watch(frame, model, True, mp3file)

        cv2.imshow("demo", frame)
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
    parser = argparse.ArgumentParser(description='visualized ver. of webcam applications with distance measurement, eye focus timing and posture watch')
    parser.add_argument('-d', '--distance', help='enable distance measurement', action='store_true')
    parser.add_argument('-t', '--time', help='enable eye focus timing', action='store_true')
    parser.add_argument('-p', '--posture', help='enable posture watching', action='store_true')
    args = parser.parse_args()

    # if any of the arguments is True
    if any([value for key, value in vars(args).items()]):
        do_applications(dist_measure=args.distance, focus_time=args.time, post_watch=args.posture)
    else:
        parser.print_help()
