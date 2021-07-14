import cv2
import numpy
import tkinter as tk

from lib.color import *
from lib.cv_font import *
from lib.draw import *
from lib.face_distance_detector import FaceDistanceDetector
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from lib.video_writer import VideoWriter
from path import to_abs_path

"""variables (should be set by the user)"""
face_to_cam_dist_in_ref: float = 45  # centi-meter
personal_face_width: float = 12.5  # centi-meter
ref_image_path: str = "img/ref_img.jpg"
warn_dist: int = 40  # centi-meter

"""initialize the detection objects"""
webcam = cv2.VideoCapture(0)
distance_detector = FaceDistanceDetector(cv2.imread(to_abs_path(ref_image_path)),
                                         face_to_cam_dist_in_ref,
                                         personal_face_width)
gaze = GazeTracking()
timer = Timer()

warning_message = cv2.imread(to_abs_path("img/warning.jpg"))

timer_width = 192 # width of timer
timer_height = 85 # height of timer

root = tk.Tk()
screen_width = root.winfo_screenwidth() # width of screen
screen_height = root.winfo_screenheight() # height of screen

timer.start()

while webcam.isOpened() and cv2.waitKey(1) != 27:  # ESC
    _, frame = webcam.read()
    bg = cv2.imread(to_abs_path("img/timer_bg.jpg"))
    bg = cv2.resize(bg, (timer_width, timer_height))
    
    """do distance measurement"""
    distance_detector.estimate(frame)
    frame = distance_detector.annotated_frame()

    text: str = ""
    if distance_detector.has_face:
        distance = distance_detector.distance()
        text = str(round(distance, 2))
        if distance < warn_dist:
            # show the warning window at the center of the screen
            warning = "warning"
            cv2.namedWindow(warning)
            cv2.moveWindow(warning, int(screen_width/2 - 245.5), int(screen_height/2 - 80.5))
            cv2.imshow(warning, warning_message)
        elif cv2.getWindowProperty("warning", cv2.WND_PROP_VISIBLE) >= 1:
            # if warning window is on the screen and the distance becomes proper, remove the windowS
            cv2.destroyWindow("warning")

    """detect faces"""
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(frame)
    frame = gaze.annotated_frame()

    # If face and gaze are not detected, pause the timer
    if not distance_detector.has_face and not gaze.pupils_located:
        timer.pause()
    else:
        timer.start()
    draw_time_stamp(bg, timer)

    """show result"""
    # Output the timer on the upper right corner
    demo = "demo"
    cv2.namedWindow(demo)
    cv2.moveWindow(demo, screen_width - timer_width, 0)
    cv2.imshow(demo, bg)

webcam.release()
timer.reset()
cv2.destroyAllWindows()