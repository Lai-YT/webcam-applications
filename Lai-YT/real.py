import cv2
import os

from lib.color import *
from lib.cv_font import *
from lib.face_distance_detector import FaceDistanceDetector


"""variables (should be set by the user)"""
face_to_cam_dist_in_ref: float = 45  # centi-meter
personal_face_width: float = 12.5  # centi-meter
ref_image_path: str = "img/ref_img.jpg"
warn_dist: int = 45  # centi-meter


cwd: str = os.path.abspath(os.path.dirname(__file__))
ref_image_path = os.path.abspath(os.path.join(cwd, ref_image_path))

webcam = cv2.VideoCapture(0)
distance_detector = FaceDistanceDetector(cv2.imread(ref_image_path),
                                         face_to_cam_dist_in_ref,
                                         personal_face_width)

while webcam.isOpened():
    _, frame = webcam.read()

    distance_detector.estimate(frame)
    distance = distance_detector.distance()
    text: str = ""
    if distance is None:
        text = "No face detected."
    else:
        text = str(round(distance, 2))
    cv2.putText(frame, text, (60, 60), FONT_3, 0.9, MAGENTA, 1)
    cv2.imshow("frame", frame)
    # ESC
    if cv2.waitKey(1) == 27:
        break

webcam.release()
cv2.destroyAllWindows()
