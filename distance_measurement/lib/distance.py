import cv2
from numpy import ndarray
from typing import Tuple, Union

from .color import *
from .cv_font import *

'''
Need some more adjustment on the distance_level of "energy bar".
'''


# focal length finder function
def focal_length(distance_in_rf_img: float,
                 width_in_rf_img: float,
                 real_width: float) -> float:
    '''This function Calculate the focal length(distance between lens to CMOS sensor).
    @param
      distance_in_rf_img:
        distance measured from object to the Camera while Capturing Reference image
      width_in_rf_img:
        object width in the frame /image in our case in the reference image(found by Face detector)
      real_width:
        Actual width (cm) of object, in real world
    @retrun
        focal_length
    '''
    return (width_in_rf_img * distance_in_rf_img) / real_width


# distance estimation function
def distance_finder(focal_length: float,
                    real_width: float,
                    width_in_frame: float) -> float:
    '''This Function simply Estimates the distance between object and camera.
    @param
      focal_length: may be the result of the focal_length function
      real_width: Actual width (cm) of object, in real world
      width_in_frame: width of object in the image
    @return
      estimated distance
    '''
    return (real_width * focal_length) / width_in_frame


# face detection Fauction
def face_data(image: ndarray) -> Tuple[int, Union[ndarray, Tuple], Tuple[int, int]]:
    '''This function Detect Face.
    @param
      image: simply the frame
    @return
      face_width:
        width of face in the frame, which allow us to calculate the distance and
        find focal length
      face:
        upper-left x, upper-left y, height of face, width of face,
        empty tuple if no face detected
      face_center:
        face centroid_x coordinate(x) and face centroid_y coordinate(y)
    '''
    # face detector object
    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    gray_image: ndarray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces: Union[ndarray, Tuple] = (
        face_detector.detectMultiScale(gray_image, 1.3, 5))  # type: ndarray[int, int, int, int]
    face_width: int = 0
    face_center: Tuple[int, int] = None

    for (x, y, h, w) in faces:
        face_width = w
        face_center = (int(w/2)+x, int(h/2)+y)

    return face_width, faces, face_center


def draw_face_area(image: ndarray, faces: ndarray) -> None:
    '''Draw a Rectangle to indicate the face.
    @param
      image: simply the frame
      face: upper-left x, upper-left y, height of face, width of face
    '''

    for (x, y, h, w) in faces:
        line_thickness: int = 2
        LLV = int(h*0.12)

        # cv2.rectangle(image, (x, y), (x+w, y+h), BLACK, 1)
        cv2.line(image, (x, y+LLV), (x+w, y+LLV), (GREEN), line_thickness)
        cv2.line(image, (x, y+h), (x+w, y+h), (GREEN), line_thickness)
        cv2.line(image, (x, y+LLV), (x, y+LLV*2), (GREEN), line_thickness)
        cv2.line(image, (x+w, y+LLV), (x+w, y+LLV*2),
                 (GREEN), line_thickness)
        cv2.line(image, (x, y+h), (x, y+h-LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w, y+h), (x+w, y+h-LLV), (GREEN), line_thickness)


def show_distance_bar(image: ndarray, faces: ndarray, distance: float) -> None:
    '''Show a bar above the face.
    The closer the face is, the longer the inner bar is.
    @param
      image: simply the frame
      face: upper-left x, upper-left y, height of face, width of face
      distance_level:
        which change the line according the distance changes (Interactivate)
    '''
    distance = round(distance, 2)
    distance_level = int(distance)
    if distance_level < 10:
        distance_level = 10

    for (x, y, h, w) in faces:
        cv2.line(image, (x, y-11), (x+180, y-11), (ORANGE), 28)
        cv2.line(image, (x, y-11), (x+180, y-11), (YELLOW), 20)
        cv2.line(image, (x, y-11), (x+180-distance_level, y-11), (GREEN), 18)

        face_center: Tuple[int, int] = (int(w/2)+x, int(h/2)+y)
        cv2.circle(image, face_center, 5, (MAGENTA), 1)
        cv2.putText(image, f'distance {distance} cm',
                    (x-6, y-6), font_3, 0.5, (BLACK), 2)
