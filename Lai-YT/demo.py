import cv2
import numpy
import os

from lib.color import *
from lib.cv_font import *
from lib.draw import *
from lib.face_distance_detector import FaceDistanceDetector
from lib.gaze_tracking import GazeTracking
from lib.timer import Timer
from lib.video_writer import VideoWriter


"""variables (should be set by the user)"""
face_to_cam_dist_in_ref: float = 45  # centi-meter
personal_face_width: float = 12.5  # centi-meter
ref_image_path: str = "img/ref_img.jpg"
to_draw_dist_bar: bool = True
warn_dist: int = 45  # centi-meter

cwd: str = os.path.abspath(os.path.dirname(__file__))
ref_image_path = os.path.abspath(os.path.join(cwd, ref_image_path))

"""initialize the detection objects"""
webcam = cv2.VideoCapture(0)
distance_detector = FaceDistanceDetector(cv2.imread(ref_image_path),
                                         face_to_cam_dist_in_ref,
                                         personal_face_width)
gaze = GazeTracking()
timer = Timer()

# output_video_path: str = os.path.abspath(os.path.join(cwd, "output_video.avi"))
# # Due to the slow writing rate, the fps can't be too high and might be machine depending.
# video_writer = VideoWriter(output_video_path, fps=7)

timer.start()

while webcam.isOpened():
    _, frame = webcam.read()

    """do distance measurement"""
    distance_detector.estimate(frame)
    frame = distance_detector.annotated_frame()

    text: str = ""
    color: BGR = None
    if distance_detector.has_face:
        distance = distance_detector.distance()
        text = str(round(distance, 2))
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
    # ESC
    if cv2.waitKey(1) == 27:
        break

webcam.release()
# video_writer.release()
timer.reset()
cv2.destroyAllWindows()
