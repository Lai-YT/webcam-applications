import cv2
import numpy
import tkinter as tk
from nptyping import Float, Int, NDArray
from playsound import playsound
from tensorflow.keras import models
from typing import Any, Tuple

from .angle_calculator import AngleCalculator
from .color import BLACK, WHITE
from .cv_font import FONT_3
from .distance_calculator import DistanceCalculator
from .image_type import ColorImage, GrayImage
from .path import to_abs_path
from .timer import Timer
from .train import PostureLabel, IMAGE_DIMENSIONS

# window position config
root = tk.Tk()
screen_width:  int = root.winfo_screenwidth()
screen_height: int = root.winfo_screenheight()
screen_center: Tuple[int, int] = (
int(screen_width/2 - 245.5), int(screen_height/2 - 80.5))

# for eye focus timing
timer_width:  int = 192
timer_height: int = 85
timer_bg: ColorImage = cv2.imread(to_abs_path("../img/timer_bg.jpg"))
timer_bg = cv2.resize(timer_bg, (timer_width, timer_height))
timer_window_name: str = "timer"
timer_window_pos: Tuple[int, int] = (screen_width - timer_width, 0)  # upper right
# break countdown
break_width:  int = 580
break_height: int = 315
break_bg: ColorImage = cv2.imread(to_abs_path("../img/break_bg.jpg"))
break_bg = cv2.resize(break_bg, (break_width, break_height))
break_window_name: str = "break time"

# for distance measurement
message_width:  int = 490
message_height: int = 160
warning_message: ColorImage = cv2.imread(to_abs_path("../img/warning.jpg"))
warning_message = cv2.resize(warning_message, (message_width, message_height))
warning_window_name: str = "warning"

# for posture watching
mp3file: str = to_abs_path("sounds/what.mp3")


def update_time_window(time: float) -> None:
    """Show a time window "min : sec" at the upper right corner of the screen.

    Arguments:
        time (float): The current time (sec) to update
    """

    timer_window: ColorImage = timer_bg.copy()
    time_duration: str = f"{(time // 60):02d}:{(time % 60):02d}"
    cv2.putText(timer_window, time_duration, (2, 70), FONT_3, 2, WHITE, 2)

    cv2.namedWindow(timer_window_name)
    cv2.moveWindow(timer_window_name, *timer_window_pos)
    cv2.imshow(timer_window_name, timer_window)


def break_time_if_too_long(timer: Timer, time_limit: int, break_time: int, camera: cv2.VideoCapture) -> None:
    """If the time record in the Timer object exceeds time limit, a break time countdown window shows on the center of screen.
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
        break_time_window: ColorImage = break_bg.copy()
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


def warn_if_angle_exceeds_threshold(angle: float, threshold: float) -> None:
    if angle > threshold:
        playsound(mp3file)


def warn_if_too_close(distance: float, warn_dist: float) -> None:
    """Warning message shows in the center of screen when the distance is less than warn_dist.

    Arguments:
        distance (float)
        warn_dist (float)
    """
    if distance < warn_dist:
        cv2.namedWindow(warning_window_name)
        cv2.moveWindow(warning_window_name, *screen_center)
        cv2.imshow(warning_window_name, warning_message)
    elif cv2.getWindowProperty(warning_window_name, cv2.WND_PROP_VISIBLE):
        cv2.destroyWindow(warning_window_name)


def warn_if_slumped(frame: ColorImage, mymodel: models) -> None:
    """mp3 will be played when posture slumpled.

    Arguments:
        frame (NDArray[(Any, Any, 3), UInt8]): Contains posture to be watched
        mymodel (tensorflow.keras.Model): Predicts the label of frame
    """
    im: GrayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    im = cv2.resize(im, IMAGE_DIMENSIONS)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *IMAGE_DIMENSIONS, 1)

    predictions: NDArray[(2,), Float[32]] = mymodel.predict(im)
    label_pred: Int[64] = numpy.argmax(predictions)

    if label_pred == PostureLabel.slump.value:
        playsound(mp3file)
