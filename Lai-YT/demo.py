import cv2
import numpy
import tkinter as tk
from typing import List

from lib.color import *
from lib.cv_font import *
from lib.draw import *
from lib.face_distance_detector import FaceDistanceDetector
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from lib.video_writer import VideoWriter
from path import to_abs_path


"""parameters set by the user"""
ref_image_path: str = "img/ref_img.jpg"
params: List[float] = []
with open(to_abs_path("parameters.txt")) as f:
    for line in f:
        params.append(float(line.rstrip('\n').split()[-1]))
face_to_cam_dist_in_ref: float = params[0]
personal_face_width: float = params[1]

"""initialize the detection objects"""
webcam = cv2.VideoCapture(0)
distance_detector = FaceDistanceDetector(cv2.imread(to_abs_path(ref_image_path)),
                                         face_to_cam_dist_in_ref,
                                         personal_face_width)
gaze = GazeTracking()
timer = Timer()
# video_writer = VideoWriter(to_abs_path("output_video.avi"))

timer.start()

while webcam.isOpened() and cv2.waitKey(1) != 27:  # ESC
    _, frame = webcam.read()

    """do distance measurement"""
    distance_detector.estimate(frame)
    frame = distance_detector.annotated_frame()

    text: str = ""
    if distance_detector.has_face:
        distance = distance_detector.distance()
        text = str(int(distance))
    else:
        text = "No face detected."
    cv2.putText(frame, text, (60, 60), FONT_3, 0.9, MAGENTA, 1)

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
    time_duration: str = f"{(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(frame, time_duration, (500, 20), FONT_3, 0.8, BLUE, 1)

    """show visualized detection result"""
    cv2.imshow("demo", frame)
    # video_writer.write(frame)

webcam.release()
# video_writer.release()
timer.reset()
cv2.destroyAllWindows()
