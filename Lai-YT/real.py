import cv2
import os

from lib.color import *
from lib.cv_font import *
from lib.face_distance_detector import FaceDistanceDetector
from path import to_abs_path


"""variables (should be set by the user)"""
face_to_cam_dist_in_ref: float = 45  # centi-meter
personal_face_width: float = 12.5  # centi-meter
ref_image_path: str = "img/ref_img.jpg"
warn_dist: int = 40  # centi-meter


webcam = cv2.VideoCapture(0)
distance_detector = FaceDistanceDetector(cv2.imread(to_abs_path(ref_image_path)),
                                         face_to_cam_dist_in_ref,
                                         personal_face_width)
warning_message = cv2.imread(to_abs_path("img/warning.png"))

while webcam.isOpened() and cv2.waitKey(1) != 27:  # ESC
    _, frame = webcam.read()

    distance_detector.estimate(frame)
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

webcam.release()
cv2.destroyAllWindows()
