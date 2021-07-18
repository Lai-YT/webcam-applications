"""
Helper functions for specific draiwng conditions.
The output coordinates aren't general-purpose.
"""

import cv2
import numpy
from typing import Tuple

from .color import *
from .cv_font import *
from .gaze_tracking import GazeTracking
from .timer import Timer


def draw_distance_bar(image: numpy.ndarray, face: Tuple[int, int, int, int],
                      distance: float, *, threshold: float = 0) -> None:
    """Draws a bar above the face. The closer the face is, the longer the inner bar is.

    Arguments:
        image (numpy.ndarray): simply the frame
        face (int, int, int, int): upper-left x, upper-left y, width of face, height of face
        distance (float): real distance between the user and the screen
    Keyword Arguments:
        threshold (float): When the face is closer than the threshold,
                           bar color turns into red and warning massage shows.
                           0 implicitly means no warning.
    """
    threshold = round(threshold, 2)
    distance = round(distance, 2)
    distance_level = int(distance)
    if distance_level < 10:
        distance_level = 10

    x, y, w, h = face
    # distance bar border
    cv2.line(image, (x, y-11), (x+180, y-11), ORANGE, 28)
    cv2.line(image, (x, y-11), (x+180, y-11), YELLOW, 20)

    if distance < threshold:
        # red distance bar
        cv2.line(image, (x, y-45), (x+100, y-45), RED, 22)
        cv2.line(image, (x, y-11), (x+180, y-11), RED, 18)
    else:
        # 120 with empty inner bar, full if closer than the threshold
        inner_bar_x: int = max(x, int(x + (120-distance_level)*180 / (120-threshold)))
        cv2.line(image, (x, y-11), (inner_bar_x, y-11), GREEN, 18)

    # distance bar normal message
    cv2.putText(image, f"distance {distance} cm",
                (x-3, y-6), FONT_2, 0.6, BLACK, 1)

    if distance < threshold:
        # warning messages
        cv2.putText(image, "Too Near!!", (x-3, y-40), FONT_2, 0.6, WHITE, 1)
        cv2.putText(image, "Stay farther, please.", (0, 30), FONT_2, 1, RED, 2)
    else:
        cv2.putText(image, "Proper distance", (0, 30), FONT_2, 1, BLACK, 2)


def draw_gazing_direction(image: numpy.ndarray, gaze: GazeTracking) -> None:
    """Draws where the user is gazing at: right, left, center or blinking.

    Arguments:
        image (numpy.ndarray): The image to draw on
        gaze (GazeTracking): The gaze dealing with
    """
    text: str = ""
    if gaze.is_blinking():
        text = "Blinking"
    elif gaze.is_right():
        text = "Looking right"
    elif gaze.is_left():
        text = "Looking left"
    elif gaze.is_center():
        text = "Looking center"

    cv2.putText(image, text, (0, 60), FONT_3, 1, BLUE, 2)


def draw_time_stamp(image: numpy.ndarray, timer: Timer) -> None:
    """Draws the time of the timer on the upper right of the image.
    Note that this function is designed for the timer window.

    Arguments:
        image (numpy.ndarray): The image to draw on
        timer (Timer): The timer which records the time
    """
    time_duration: str = f"{(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(image, time_duration, (2, 70), FONT_3, 2, WHITE, 2)
