import cv2
import numpy as np
import tkinter as tk
from playsound import playsound
from tensorflow.keras import models
from typing import Tuple

from .color import *
from .cv_font import *
from .face_distance_detector import FaceDistanceDetector
from .gaze_tracking import GazeTracking
from .path import to_abs_path
from .timer import Timer
from .train import PostureLabel

# type hints
Image = np.ndarray

# window position config
root = tk.Tk()
screen_width:  int = root.winfo_screenwidth()
screen_height: int = root.winfo_screenheight()
screen_center: Tuple[int, int] = (
int(screen_width/2 - 245.5), int(screen_height/2 - 80.5))

# for eye focus timing
timer_width:  int = 192
timer_height: int = 85
timer_bg: Image = cv2.imread(to_abs_path("../img/timer_bg.jpg"))
timer_bg = cv2.resize(timer_bg, (timer_width, timer_height))
timer_window_name: str = "timer"
timer_window_pos: Tuple[int, int] = (screen_width - timer_width, 0)  # upper right
# break countdown
break_width:  int = 580
break_height: int = 315
break_bg: Image = cv2.imread(to_abs_path("../img/break_bg.jpg"))
break_bg = cv2.resize(break_bg, (break_width, break_height))
break_window_name: str = "break time"

# for distance measurement
message_width:  int = 490
message_height: int = 160
warning_message: Image = cv2.imread(to_abs_path("../img/warning.jpg"))
warning_message = cv2.resize(warning_message, (message_width, message_height))
warning_window_name: str = "warning"

# for posture watching
mp3file: str = to_abs_path("sounds/what.mp3")


def update_time(timer: Timer, face_detector: FaceDistanceDetector, gaze: GazeTracking) -> None:
    """Update time in the timer and show a window at the upper right corner of the screen.
    The timer wil keep timing if there's a face or pair of eyes, otherwise stops.

    Arguments:
        timer (Timer): Contains time to be updated
        face_detector (FaceDistanceDetector): Tells whether there's a face or not
        gaze (GazeTracking): Tells whether there's a pair of eyes or not
    """
    if not face_detector.has_face and not gaze.pupils_located:
        timer.pause()
    else:
        timer.start()
    timer_window: Image = timer_bg.copy()
    time: int = timer.time()  # sec
    time_duration: str = f"{(time // 60):02d}:{(time % 60):02d}"
    cv2.putText(timer_window, time_duration, (2, 70), FONT_3, 2, WHITE, 2)

    cv2.namedWindow(timer_window_name)
    cv2.moveWindow(timer_window_name, *timer_window_pos)
    cv2.imshow(timer_window_name, timer_window)


def break_time_if_too_long(timer: Timer, time_limit: int, break_time: int, camera: cv2.VideoCapture) -> None:
    """If the time record in the Timer object exceeds time limit, a break time countdown window shows in the center of screen.
    Camera turned off and all detections stop during the break. Also the Timer resets after it.

    Arguments:
        timer (Timer): Contains time record
        time_limit (int): Triggers a break if reached (minutes)
        break_time (int): How long the break should be (minutes)
        camera (cv2.VideoCapture): Turns off during break time, reopens after the break
    """
    time_limit *= 60 # minute to second
    # not the time to take a break
    if timer.time() < time_limit:
        return
    # stops camera and all detections
    camera.release()
    timer.reset()
    cv2.destroyAllWindows()
    # break time timer
    break_timer = Timer()
    break_timer.start()
    break_time *= 60  # minute to second
    # break time countdown window
    cv2.namedWindow(break_window_name)
    cv2.moveWindow(break_window_name, *screen_center)
    while break_timer.time() < break_time:
        break_time_window: Image = break_bg.copy()
        # in sec
        countdown: int = break_time - break_timer.time()
        time_left: str = f"{(countdown // 60):02d}:{(countdown % 60):02d}"
        cv2.putText(break_time_window, str(break_time//60), (100, 175), FONT_3, 1.5, BLACK, 2)
        cv2.putText(break_time_window, time_left, (165, 287), FONT_3, 0.9, BLACK, 1)
        cv2.imshow(break_window_name, break_time_window)
        cv2.waitKey(200)  # wait since only have to update once per second
    # break time over
    cv2.destroyWindow(break_window_name)
    camera.open(0)


def warn_if_too_close(face_distance_detector: FaceDistanceDetector, warn_dist: float) -> None:
    """Warning message shows in the center of screen when the distance measured by FaceDistanceDetector is less than warn dist.

    Arguments:
        face_distance_detector (FaceDistanceDetector)
        warn_dist (float)
    """
    text: str = ""
    if face_distance_detector.has_face:
        distance: float = face_distance_detector.distance()
        text = str(int(distance))
        if distance < warn_dist:
            cv2.namedWindow(warning_window_name)
            cv2.moveWindow(warning_window_name, *screen_center)
            cv2.imshow(warning_window_name, warning_message)
        elif cv2.getWindowProperty(warning_window_name, cv2.WND_PROP_VISIBLE):
            cv2.destroyWindow(warning_window_name)


def warn_if_slumped(frame: Image, mymodel) -> None:
    """mp3 will be played when posture slumpled.

    Arguments:
        frame (numpy.ndarray): Contains posture to be watched
        mymodel (tensorflow.keras.Model): Predicts the label of frame
    """
    im: Image = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    im = cv2.resize(im, image_dimensions)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *image_dimensions, 1)

    predictions: np.ndarray = mymodel.predict(im)
    label_pred: np.int64 = np.argmax(predictions)

    if label_pred == PostureLabel.slump.value:
        playsound(mp3file)
