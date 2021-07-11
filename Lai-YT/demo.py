import cv2
import numpy as np

from lib.color import *
from lib.cv_font import *
from lib.distance import *
from lib.gaze_tracking import *


def draw_gazing_direction(gaze, output_frame) -> None:
    """Draw where the user is gazing at: right, left, center or blinking.

    Arguments:
        gaze (GazeTracking): The gaze dealing with
        output_frame (numpy.ndarray): The frame to draw direction
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

    cv2.putText(output_frame, text, (60, 30), FONT_2, 1, CYAN, 2)


"""variables (should be set by the user)"""
face_to_cam_dist_in_ref: float = 45  # centi-meter
personal_face_width: float = 12.5  # centi-meter
ref_image_path: str = "img/ref_img.jpg"
to_show_dist_bar: bool = True
warn_dist: int = 45  # centi-meter

focal_length_in_ref: float = (
    get_img_focal_length(ref_image_path, face_to_cam_dist_in_ref, personal_face_width))

"""initialize the detection objects"""
gaze = GazeTracking()
webcam = cv2.VideoCapture(0)

while True:
    _, original_frame = webcam.read()

    """do gaze tracking"""
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(original_frame)

    # This method returns a frame copy to draw on,
    # remember to make sure all following methods draw on the same frame.
    output_frame: np.ndarray = gaze.annotated_frame()

    draw_gazing_direction(gaze, output_frame)

    """do distance measurement"""
    face: np.ndarray = face_data(original_frame)

    for (x, y, w, h) in face:
        if w == 0:
            continue
        draw_face_area(output_frame, face)
        if to_show_dist_bar:
            distance: float = estimate_distance(
                focal_length_in_ref, personal_face_width, w)
            show_distance_bar(
                output_frame, face, distance, warning_threshold=warn_dist)

    """show result"""
    cv2.imshow("demo", output_frame)
    # ESC
    if cv2.waitKey(1) == 27:
        break

webcam.release()
cv2.destroyAllWindows()
