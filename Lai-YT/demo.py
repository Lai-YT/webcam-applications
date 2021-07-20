import argparse
import cv2
import numpy
import tkinter as tk
from typing import List

from lib.color import *
from lib.cv_font import *
from lib.draw import *
from lib.face_distance_detector import FaceDistanceDetector
from lib.gaze_tracking import GazeTracking
from lib.posture import *
from lib.timer import Timer
from lib.video_writer import VideoWriter
from path import to_abs_path


"""parameters set by the user"""
ref_image_path: str = to_abs_path("img/ref_img.jpg")
params: List[float] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(float(line.rstrip("\n").split()[-1]))
face_to_cam_dist_in_ref: float = params[0]
personal_face_width:     float = params[1]

"""config settings"""
model_path:   str = to_abs_path("lib/trained_models/posture_model.h5")
training_dir: str = to_abs_path("train")
mp3file:      str = to_abs_path("sounds/what.mp3")


def do_application() -> None:
    """initialize the detection objects"""
    webcam = cv2.VideoCapture(0)
    distance_detector = FaceDistanceDetector(cv2.imread(ref_image_path),
                                             face_to_cam_dist_in_ref,
                                             personal_face_width)
    gaze = GazeTracking()
    timer = Timer()
    model = load_model(model_path)
    # video_writer = VideoWriter(to_abs_path("output_video.avi"))

    timer.start()

    while webcam.isOpened() and cv2.waitKey(1) != 27:  # ESC
        _, frame = webcam.read()
        frame = cv2.flip(frame, flipCode=1)  # horizontal

        """do distance measurement"""
        distance_detector.estimate(frame)
        frame = distance_detector.annotated_frame()

        text: str = ""
        if distance_detector.has_face:
            distance = distance_detector.distance()
            text = "dist. " + str(int(distance))
        else:
            text = "No face detected."
        cv2.putText(frame, text, (60, 30), FONT_3, 0.9, MAGENTA, 1)

        """do gaze tracking"""
        # We send this frame to GazeTracking to analyze it
        gaze.refresh(frame)
        frame = gaze.annotated_frame()

        """record screen focus time"""
        if not distance_detector.has_face and not gaze.pupils_located:
            timer.pause()
            cv2.putText(frame, "timer paused", (432, 40), FONT_3, 0.6, RED, 1)
        else:
            timer.start()
        time_duration: str = f"t. {(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
        cv2.putText(frame, time_duration, (500, 20), FONT_3, 0.8, BLUE, 1)

        """posture watch"""
        frame = do_posture_watch(frame, model, True, mp3file)

        """show visualized detection result"""
        cv2.imshow("demo", frame)
        # video_writer.write(frame)

    webcam.release()
    # video_writer.release()
    timer.reset()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='webcam applications with distance measurement, eye focus timing and posture watch')
    parser.add_argument('-cg', '--capture-good', help='capture example of good, healthy posture', action='store_true')
    parser.add_argument('-cs', '--capture-slump', help='capture example of poor, slumped posture', action='store_true')
    parser.add_argument('-t', '--train', help='train model with captured images', action='store_true')
    parser.add_argument('-a', '--applications', help='visualized detection with all applications', action='store_true')
    args = parser.parse_args()

    if args.train:
        do_training(training_dir, model_path)
    elif args.applications:
        do_application()
    elif args.capture_good:
        do_capture_action(1, 'Good')
    elif args.capture_slump:
        do_capture_action(2, 'Slumped')
    else:
        parser.print_help()
