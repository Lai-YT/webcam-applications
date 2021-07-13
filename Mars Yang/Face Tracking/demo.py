import cv2
import numpy
import os

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

    time_duration: str = f"duration {(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(image, time_duration, (0, 55), FONT_2, 2, BLUE, 2)
    
def warning(image: numpy.ndarray, timer: Timer, message: str, focus_time: int) -> None:
    '''Put a message to warn user if focus time is too long.

    Arguments:
        image (numpy.ndarray): The image to draw on
        timer (Timer): The timer which records the time
        message (str): Warning message
        focus_time (int): Threshold of focus time to warn
    '''
    if timer.time() > focus_time:
        cv2.putText(image, message, (0, 150), FONT_2, 1, RED, 1)

"""variables (should be set by the user)"""
face_to_cam_dist_in_ref: float = 45  # centi-meter
personal_face_width: float = 12.5  # centi-meter
ref_image_path: str = "img/ref_img.jpg"
to_draw_dist_bar: bool = True
warn_dist: int = 40  # centi-meter

cwd: str = os.path.abspath(os.path.dirname(__file__))
ref_image_path = os.path.abspath(os.path.join(cwd, ref_image_path))

# Focal length is the imaginary distance from webcam to image
focal_length_in_ref: float = (
    get_img_focal_length(ref_image_path, face_to_cam_dist_in_ref, personal_face_width))

"""initialize the detection objects"""
gaze = GazeTracking()
webcam = cv2.VideoCapture(0)
timer = Timer()
timer.start()

while True:
    _, original_frame = webcam.read()
    bg = cv2.imread("img/bg.jpg")
    bg = cv2.resize(bg, (960, 540))
    
    """do gaze tracking"""
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(original_frame)

    # This method returns a frame copy to draw on,
    # remember to make sure all following methods draw on the same frame.
    output_frame: numpy.ndarray = gaze.annotated_frame()

    """do distance measurement"""
    faces: numpy.ndarray = face_data(original_frame)

    # If gaze is not detected, pause the timer
    if len(faces) == 0:
        timer.pause()
        cv2.putText(bg, "Face not detected", (0, 55), FONT_2, 2, RED, 2)
    else:
        timer.start()
        """record screen focus time"""
        draw_time_stamp(bg, timer)

    # If focus time is too long, put a message to warn user
    warning_message: str = "Focusing on the screen too long"
    warning(bg, timer, warning_message, 5)

    # detect the distance and give warning if too close to screen
    for (x, y, w, h) in faces:
        distance: float = estimate_distance(focal_length_in_ref, personal_face_width, w)
        if distance < warn_dist:
            # warning message
            cv2.putText(bg, "Stay farther, please.", (5, 90), FONT_2, 1, RED, 1)
    

    """show result"""
    cv2.imshow("demo", bg)
    # ESC
    if cv2.waitKey(1) == 27:
        break

webcam.release()
timer.reset()
cv2.destroyAllWindows()
