import argparse
import cv2
import numpy
from face_recognition import face_locations
from typing import Any, Dict, List

import lib.app_visual as vs
from lib.face_distance_detector import DistanceDetector, FaceDetector
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from lib.train import PostureMode, load_posture_model
from path import to_abs_path


def draw_face_area(frame, *, color = (255, 0, 0)) -> numpy.ndarray:
    """Returns the frame with the face indicated with angles.

    Keyword Arguments:
        color (color.BGR): Color of the lines, green (0, 255, 0) in default
    """
    frame: numpy.ndarray = frame.copy()
    face_location = face_locations(frame)
    for upper_y, lower_x, lower_y, upper_x in face_location:
        x, y, w, h = upper_x, upper_y, lower_x - upper_x, lower_y - upper_y
        line_thickness: int = 2
        # affects the length of corner line
        LLV = int(h*0.12)

        # vertical corner lines
        cv2.line(frame, (x, y+LLV), (x+LLV, y+LLV), color, line_thickness)
        cv2.line(frame, (x+w-LLV, y+LLV), (x+w, y+LLV), color, line_thickness)
        cv2.line(frame, (x, y+h), (x+LLV, y+h), color, line_thickness)
        cv2.line(frame, (x+w-LLV, y+h), (x+w, y+h), color, line_thickness)

        # horizontal corner lines
        cv2.line(frame, (x, y+LLV), (x, y+LLV+LLV), color, line_thickness)
        cv2.line(frame, (x+w, y+LLV), (x+w, y+LLV+LLV), color, line_thickness)
        cv2.line(frame, (x, y+h), (x, y+h-LLV), color, line_thickness)
        cv2.line(frame, (x+w, y+h), (x+w, y+h-LLV), color, line_thickness)
    return frame


"""parameters set by the user"""
ref_image_path: str = to_abs_path("img/ref_img.jpg")
params: List[float] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(float(line.rstrip("\n").split()[-1]))
face_to_cam_dist_in_ref: float = params[0]
personal_face_width:     float = params[1]


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
            cv2.imread(ref_image_path), face_to_cam_dist_in_ref, personal_face_width)
    if post_watch:
        models: Dict[PostureMode, Any] = load_posture_model()
    if focus_time:
        timer = Timer()
        timer.start()

    while webcam.isOpened():
        _, frame = webcam.read()
        frame = cv2.flip(frame, flipCode=1)  # mirrors, so horizontally flip

        # commons
        if dist_measure or post_watch or focus_time:
            face_detector.refresh(frame)
            frame = face_detector.annotated_frame()
        if post_watch or focus_time:
            gaze.refresh(frame)
            frame = gaze.annotated_frame()

        if dist_measure:
            distance_detector.estimate(frame)
            frame = vs.do_distance_measurement(frame, distance_detector)
        if post_watch:
            if face_detector.has_face or gaze.pupils_located:
                mode = PostureMode.gaze
            else:
                mode = PostureMode.write
            frame = vs.do_posture_watch(frame, models[mode], mode)
        if focus_time:
            frame = vs.do_focus_time_record(frame, timer, face_detector, gaze)

        # face_recognition
        frame = draw_face_area(frame)

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
