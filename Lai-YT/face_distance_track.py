import cv2
from numpy import ndarray

from lib.distance import *


"""variables (should be set by the user)"""
# distance from camera to object(face) measured
known_distance: float = 45  # centi-meter
# mine is 14.3 something, measure your face width, or google it
known_width: float = 12.5  # centi-meter
# a reference image of your face for calculating the distance
ref_image_path: str = "img/ref_img.jpg"
# To show the distance bar or not.
call_out: bool = True
# warns when the distance is shorter than threshold
warning: int = 45  # centi-meter

focal_length_found: float = (
    get_img_focal_length(ref_image_path, known_distance, known_width))

# Camera Object
webcam = cv2.VideoCapture(0)  # Number According to your Camera

while True:
    _, frame = webcam.read()

    faces: ndarray = face_data(frame)  # type: ndarray[int, int, int, int]

    # finding the distance by calling function distance finder
    for (face_x, face_y, face_w, face_h) in faces:
        if face_w == 0:
            continue
        draw_face_area(frame, faces)
        if call_out:
            distance: float = estimate_distance(
                focal_length_found, known_width, face_w)
            show_distance_bar(
                frame, faces, distance, warning_threshold=warning)
    cv2.imshow("frame", frame)
    key: int = cv2.waitKey(5)
    # q: end detection
    if key == ord("q"):
        break

webcam.release()
cv2.destroyAllWindows()
