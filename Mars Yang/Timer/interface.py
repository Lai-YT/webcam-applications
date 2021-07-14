import cv2
import numpy
import os
import tkinter as tk

from lib.color import *
from lib.cv_font import *
from lib.distance import *
from lib.gaze_tracking import GazeTracking
from lib.timer import *

def draw_time_stamp(image: numpy.ndarray, timer: Timer) -> None:
    """Draw the time of the timer on the upper right of the image.

    Arguments:
        image (numpy.ndarray): The image to draw on
        timer (Timer): The timer which records the time
    """

    time_duration: str = f"{(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(image, time_duration, (5, 60), FONT_2, 2, WHITE, 2)

"""initialize the detection objects"""
gaze = GazeTracking()
webcam = cv2.VideoCapture(0)
timer = Timer()
timer_width = 192 # width of timer
timer_height = 85 # height of timer
timer.start()

while True:
    _, original_frame = webcam.read()
    bg = cv2.imread("img/timer_bg.jpg")
    bg = cv2.resize(bg, (timer_width, timer_height))
    
    """detect faces"""
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(original_frame)
    faces: numpy.ndarray = face_data(original_frame)

    # If gaze is not detected, pause the timer
    draw_time_stamp(bg, timer)
    if len(faces) == 0:
        timer.pause()
    else:
        timer.start()

    """show result"""
    # Output the timer on the upper right corner
    root = tk.Tk()
    screen_width = root.winfo_screenwidth()
    interface = "interface"
    cv2.namedWindow(interface)
    cv2.moveWindow(interface, screen_width - timer_width, 0)
    cv2.imshow(interface, bg)
    # ESC
    if cv2.waitKey(1) == 27:
        break

webcam.release()
timer.reset()
cv2.destroyAllWindows()