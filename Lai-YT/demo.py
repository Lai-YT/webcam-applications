import cv2
import numpy
import os
import time

from lib.color import *
from lib.cv_font import *
from lib.distance import *
from lib.gaze_tracking import GazeTracking
from lib.timer import *


def draw_gazing_direction(image: numpy.ndarray, gaze: GazeTracking) -> None:
    """Draw where the user is gazing at: right, left, center or blinking.

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

    cv2.putText(image, text, (60, 60), FONT_2, 1, CYAN, 2)


def draw_time_stamp(image: numpy.ndarray, timer: Timer) -> None:
    """Draw the time of the timer on the upper right of the image.

    Arguments:
        image (numpy.ndarray): The image to draw on
        timer (Timer): The timer which records the time
    """
    time_duration: str = f"duration: {timer.time() // 60}m {timer.time() % 60}s"
    cv2.putText(image, time_duration, (400, 30), FONT_3, 0.6, BLUE, 1)


"""variables (should be set by the user)"""
face_to_cam_dist_in_ref: float = 45  # centi-meter
personal_face_width: float = 12.5  # centi-meter
ref_image_path: str = "img/ref_img.jpg"
to_draw_dist_bar: bool = True
warn_dist: int = 45  # centi-meter

cwd: str = os.path.abspath(os.path.dirname(__file__))
ref_image_path = os.path.abspath(os.path.join(cwd, ref_image_path))

focal_length_in_ref: float = (
    get_img_focal_length(ref_image_path, face_to_cam_dist_in_ref, personal_face_width))

"""initialize the detection objects"""
gaze = GazeTracking()
webcam = cv2.VideoCapture(0)
timer = Timer()

timer.start()

while True:
    _, original_frame = webcam.read()

    """do gaze tracking"""
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(original_frame)

    # This method returns a frame copy to draw on,
    # remember to make sure all following methods draw on the same frame.
    output_frame: numpy.ndarray = gaze.annotated_frame()

    draw_gazing_direction(output_frame, gaze)

    """do distance measurement"""
    faces: numpy.ndarray = face_data(original_frame)

    if len(faces) == 0:
        timer.pause()
    for (x, y, w, h) in faces:
        timer.start()
        draw_face_area(output_frame, faces)
        if to_draw_dist_bar:
            distance: float = estimate_distance(focal_length_in_ref, personal_face_width, w)
            draw_distance_bar(output_frame, faces, distance, threshold=warn_dist)

    """record screen focus time"""
    draw_time_stamp(output_frame, timer)

    """show result"""
    cv2.imshow("demo", output_frame)
    # ESC
    if cv2.waitKey(1) == 27:
        break

webcam.release()
timer.reset()
cv2.destroyAllWindows()
