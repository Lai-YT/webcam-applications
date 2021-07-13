import cv2
from numpy import ndarray
from typing import Tuple, Union

from .color import *
from .cv_font import *


def get_img_focal_length(image_path: str, distance: float, width: float) -> float:
    """Returns the distance between lens to CMOS sensor in the img.

    Arguments:
        image_path: absolue path of the image
        distance: real distance between object and camera
        width: real width of the object
    """
    image: ndarray = cv2.imread(image_path)
    object_width: int = 0
    for (_, _, w, _) in face_data(image):
        object_width = w
    return focal_length(distance, width, object_width)


# @tech: similar triangles
#   width_in_rf_img : width = focal_length : distance
# =>width_in_rf_img * distance = width * focal_length
# =>focal_length = (width_in_rf_img * distance) / width
def focal_length(distance: float, width: float, width_in_rf_img: float) -> float:
    """Returns the distance between lens to CMOS sensor.

    Arguments:
        distance: real distance between object and camera
        width_in_rf_img: object width in the frame/image in our case in the
                         reference image(found by Face detector)
        width: The actual width (cm) of object in real world
    """
    return (width_in_rf_img * distance) / width


# @tech: similar triangles
#   width_in_frame : real_width = focal_length : estimated distance
# =>width_in_frame * estimated distance = real_width * focal_length
# =>estimated distance = (real_width * focal_length) / width_in_frame
def estimate_distance(focal_length: float, real_width: float, width_in_frame: float) -> float:
    """Returns the estimated distance between object and camera.

    Arguments:
        focal_length: may be the result of the focal_length function
        real_width: Actual width (cm) of object, in real world
        width_in_frame: width of object in the image
    """
    return (real_width * focal_length) / width_in_frame


def face_data(image: ndarray) -> Tuple[int, Union[ndarray, Tuple]]:
    """This function detect face from an image.

    Arguments:
        image: simply the frame

    Returns:
        face_width: width of face in the frame, which allow us to calculate the
                    distance and find focal length
        faces: upper-left x, upper-left y, width of face, height of face,
               empty tuple if no face detected
    """
    # face detector object
    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    gray_image: ndarray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces: Union[ndarray, Tuple] = face_detector.detectMultiScale(gray_image, 1.3, 5)

    return faces