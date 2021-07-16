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
warn_dist: float = params[2]

"""initialize the detection objects"""
webcam = cv2.VideoCapture(0)
distance_detector = FaceDistanceDetector(cv2.imread(to_abs_path(ref_image_path)),
                                         face_to_cam_dist_in_ref,
                                         personal_face_width)
gaze = GazeTracking()
timer = Timer()
root = tk.Tk()


Image = numpy.ndarray
"""designed variables"""
warning_message: Image = cv2.imread(to_abs_path("img/warning.jpg"))
screen_width: int = root.winfo_screenwidth()
screen_height: int = root.winfo_screenheight()
screen_center: Tuple[int, int] = (
    int(screen_width/2 - 245.5), int(screen_height/2 - 80.5))
timer_width:  int = 192
timer_height: int = 85
timer_bg: Image = cv2.imread(to_abs_path("img/timer_bg.jpg"))
timer_bg = cv2.resize(timer_bg, (timer_width, timer_height))
timer_window_name: str = "timer"
warning_window_name: str = "warning"
# upper right
timer_window_pos: Tuple[int, int] = (screen_width - timer_width, 0)

timer.start()

while webcam.isOpened() and cv2.waitKey(1) != 27:  # ESC
    _, frame = webcam.read()

    """do distance measurement"""
    distance_detector.estimate(frame)

    text: str = ""
    if distance_detector.has_face:
        distance = distance_detector.distance()
        text = str(int(distance))
        if distance < warn_dist:
            cv2.namedWindow(warning_window_name)
            cv2.moveWindow(warning_window_name, *screen_center)
            cv2.imshow(warning_window_name, warning_message)
        elif cv2.getWindowProperty(warning_window_name, cv2.WND_PROP_VISIBLE):
            cv2.destroyWindow(warning_window_name)

    """do gaze tracking"""
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(frame)

    """record screen focus time"""
    if not distance_detector.has_face and not gaze.pupils_located:
        timer.pause()
    else:
        timer.start()
    timer_window: Image = timer_bg.copy()
    draw_time_stamp(timer_window, timer)
    cv2.namedWindow(timer_window_name)
    cv2.moveWindow(timer_window_name, *timer_window_pos)
    cv2.imshow(timer_window_name, timer_window)

webcam.release()
timer.reset()
cv2.destroyAllWindows()
