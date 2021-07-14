import cv2
import numpy

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

# video_writer = VideoWriter(to_abs_path("output_video.avi"))
warning_message = cv2.imread(to_abs_path("img/warning.png"))

timer.start()

while webcam.isOpened() and cv2.waitKey(1) != 27:  # ESC
    _, frame = webcam.read()

    """do distance measurement"""
    distance_detector.estimate(frame)
    frame = distance_detector.annotated_frame()

    text: str = ""
    if distance_detector.has_face:
        distance = distance_detector.distance()
        text = str(round(distance, 2))
        if distance < warn_dist:
            cv2.imshow("warning", warning_message)
        else:
            cv2.destroyWindow("warning")
    else:
        text = "No face detected."
    cv2.putText(frame, text, (60, 60), FONT_3, 0.9, MAGENTA, 1)

    """do gaze tracking"""
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(frame)
    frame = gaze.annotated_frame()

    """record screen focus time"""
    if not distance_detector.has_face and not gaze.pupils_located:
        timer.pause()
        cv2.putText(frame, "timer paused", (432, 40), FONT_3, 0.6, RED, 1)
    else:
        timer.start()
    draw_time_stamp(frame, timer)

    """show result"""
    cv2.imshow("demo", frame)
    # video_writer.write(frame)

webcam.release()
# video_writer.release()
timer.reset()
cv2.destroyAllWindows()
