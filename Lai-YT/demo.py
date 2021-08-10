import argparse
import cv2
from typing import Any, Dict, List

import lib.app as app
from lib.distance_detector import DistanceDetector
from lib.face_detector import FaceDetector
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from lib.train import PostureMode, load_posture_model
from path import to_abs_path


"""parameters set by the user"""
params: List[str] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(line.rstrip('\n').split()[-1])

face_dist_in_ref = float(params[0])
real_face_width = float(params[1])
warn_dist = float(params[2])
time_limit = int(params[3])
break_time = int(params[4])
ref_image_path: str = to_abs_path("img/ref_img.jpg")


def do_applications(*, dist_measure: bool, focus_time: bool, post_watch: bool) -> None:
    """Enable the applications that are marked True."""
    # Initializations
    webcam = cv2.VideoCapture(0)

    # commons
    if post_watch or focus_time:
        face_detector = FaceDetector()
        gaze = GazeTracking()

    if dist_measure:
        distance_detector = DistanceDetector(
            cv2.imread(ref_image_path), face_dist_in_ref, real_face_width)
    if post_watch:
        models: Dict[PostureMode, Any] = load_posture_model()
    if focus_time:
        timer = Timer()
        timer.start()
    # Do
    while webcam.isOpened():
        _, frame = webcam.read()

        # commons
        if post_watch or focus_time:
            face_detector.refresh(frame)
            gaze.refresh(frame)

        if dist_measure:
            distance_detector.estimate(frame)
            app.warn_if_too_close(distance_detector, warn_dist)
        if post_watch:
            if face_detector.has_face or gaze.pupils_located:
                mode = PostureMode.gaze
            else:
                mode = PostureMode.write
            app.warn_if_slumped(frame, models[mode])
        if focus_time:
            if not face_detector.has_face and not gaze.pupils_located:
                timer.pause()
            else:
                timer.start()
            app.update_time(timer)
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
