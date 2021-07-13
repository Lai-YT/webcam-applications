import cv2
import numpy
import os

from lib.color import *
from lib.cv_font import *
from lib.distance import *
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from lib.video_writer import VideoWriter


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

    cv2.putText(image, text, (0, 60), FONT_3, 1, BLUE, 2)


def draw_time_stamp(image: numpy.ndarray, timer: Timer) -> None:
    """Draw the time of the timer on the upper right of the image.

    Arguments:
        image (numpy.ndarray): The image to draw on
        timer (Timer): The timer which records the time
    """
    time_duration: str = f"duration {(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(image, time_duration, (432, 20), FONT_3, 0.8, BLUE, 1)


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

output_video_path: str = os.path.abspath(os.path.join(cwd, "output_video.avi"))
# Due to the slow writing rate, the fps can't be too high and might be machine depending.
video_writer = VideoWriter(output_video_path, fps=7)

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

    if len(faces) == 0 and not gaze.pupils_located:
        timer.pause()
        cv2.putText(output_frame, "timer paused", (432, 40), FONT_3, 0.6, RED, 1)
    else:
        timer.start()
    for (x, y, w, h) in faces:
        draw_face_area(output_frame, faces)
        if to_draw_dist_bar:
            distance: float = estimate_distance(focal_length_in_ref, personal_face_width, w)
            draw_distance_bar(output_frame, faces, distance, threshold=warn_dist)

    """record screen focus time"""
    draw_time_stamp(output_frame, timer)

    """show result"""
    cv2.imshow("demo", output_frame)
    video_writer.write(output_frame)
    # ESC
    if cv2.waitKey(1) == 27:
        break

webcam.release()
video_writer.release()
timer.reset()
cv2.destroyAllWindows()
