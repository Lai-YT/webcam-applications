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


def draw_face_area(image: ndarray, faces: ndarray) -> None:
    """Draw angles to indicate the face.

    Arguments:
        image: simply the frame
        face: upper-left x, upper-left y, width of face, height of face
    """
    for (x, y, w, h) in faces:
        line_thickness: int = 2
        # affects the length of corner line
        LLV = int(h*0.12)

        # vertical corner lines
        cv2.line(image, (x, y+LLV), (x+LLV, y+LLV), GREEN, line_thickness)
        cv2.line(image, (x+w-LLV, y+LLV), (x+w, y+LLV), GREEN, line_thickness)
        cv2.line(image, (x, y+h), (x+LLV, y+h), GREEN, line_thickness)
        cv2.line(image, (x+w-LLV, y+h), (x+w, y+h), GREEN, line_thickness)

        # horizontal corner lines
        cv2.line(image, (x, y+LLV), (x, y+LLV+LLV), GREEN, line_thickness)
        cv2.line(image, (x+w, y+LLV), (x+w, y+LLV+LLV), GREEN, line_thickness)
        cv2.line(image, (x, y+h), (x, y+h-LLV), GREEN, line_thickness)
        cv2.line(image, (x+w, y+h), (x+w, y+h-LLV), GREEN, line_thickness)


def draw_distance_bar(image: ndarray, faces: ndarray, distance: float,
                      *, threshold: float = 0) -> None:
    """Draw a bar above the face.
    The closer the face is, the longer the inner bar is.

    Arguments:
        image: simply the frame
        face: upper-left x, upper-left y, width of face, height of face
        distance: real distance between the user and the screen
    Keyword Arguments:
        threshold: When the face is closer than the threshold,
                   bar color turns into red and warning massage shows.
                   0 implicitly means no warning.
    """
    threshold = round(threshold, 2)
    distance = round(distance, 2)
    distance_level = int(distance)
    if distance_level < 10:
        distance_level = 10

    for (x, y, w, h) in faces:
        # distance bar border
        cv2.line(image, (x, y-11), (x+180, y-11), ORANGE, 28)
        cv2.line(image, (x, y-11), (x+180, y-11), YELLOW, 20)

        if distance < threshold:
            # red distance bar
            cv2.line(image, (x, y-45), (x+100, y-45), RED, 22)
            cv2.line(image, (x, y-11), (x+180, y-11), RED, 18)
        else:
            # 120 with empty inner bar, full if closer than the threshold
            inner_bar_x: int = max(x, int(x + (120-distance_level)*180 / (120-threshold)))
            cv2.line(image, (x, y-11), (inner_bar_x, y-11), GREEN, 18)

        # distance bar normal message
        cv2.putText(image, f"distance {distance} cm",
                    (x-3, y-6), FONT_2, 0.6, BLACK, 1)

        if distance < threshold:
            # warning messages
            cv2.putText(image, "Too Near!!", (x-3, y-40), FONT_2, 0.6, WHITE, 1)
            cv2.putText(image, "Stay farther, please.", (0, 30), FONT_2, 1, RED, 2)
        else:
            cv2.putText(image, "Proper distance", (0, 30), FONT_2, 1, BLACK, 2)
