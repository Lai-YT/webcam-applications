import cv2
from numpy import ndarray
from typing import Tuple, Union

from lib.color import *
from lib.cv_font import *

'''
Need some more adjustment on the distance_level of "distance bar".
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
def face_data(image: ndarray) -> Tuple[int, Union[ndarray, Tuple]]:
    '''This function Detect Face.
    @param
      image: simply the frame
    @return
      face_width:
        width of face in the frame, which allow us to calculate the distance and
        find focal length
      faces:
        upper-left x, upper-left y, width of face, height of face,
        empty tuple if no face detected
    '''
    # face detector object
    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    gray_image: ndarray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces: Union[ndarray, Tuple] = (
        face_detector.detectMultiScale(gray_image, 1.3, 5))  # type: ndarray[int, int, int, int]

    return faces


def draw_face_area(image: ndarray, faces: ndarray) -> None:
    '''Draw a Rectangle to indicate the face.
    @param
      image: simply the frame
      face: upper-left x, upper-left y, width of face, height of face
    '''

    for (x, y, w, h) in faces:
        line_thickness: int = 2
        LLV = int(h*0.12)

        # cv2.rectangle(image, (x, y), (x+w, y+h), BLACK, 1)
        cv2.line(image, (x, y+LLV), (x+LLV, y+LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w-LLV, y+LLV), (x+w, y+LLV), (GREEN), line_thickness)
        cv2.line(image, (x, y+h), (x+LLV, y+h), (GREEN), line_thickness)
        cv2.line(image, (x+w-LLV, y+h), (x+w, y+h), (GREEN), line_thickness)

        cv2.line(image, (x, y+LLV), (x, y+LLV+LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w, y+LLV), (x+w, y+LLV+LLV),
                 (GREEN), line_thickness)
        cv2.line(image, (x, y+h), (x, y+h-LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w, y+h), (x+w, y+h-LLV), (GREEN), line_thickness)



def show_distance_bar(image: ndarray, faces: ndarray, distance: float,
                      *, warning_threshold: float = 0) -> None:
    '''Show a bar above the face.
    The closer the face is, the longer the inner bar is.
    @param
      image: simply the frame
      face: upper-left x, upper-left y, width of face, height of face
      distance_level:
        which change the line according the distance changes (Interactivate)
    '''
    warning_threshold = round(warning_threshold, 2)
    distance = round(distance, 2)
    distance_level = int(distance)
    if distance_level < 10:
        distance_level = 10

    for (x, y, w, h) in faces:
        # distance bar border
        cv2.line(image, (x, y-11), (x+180, y-11), (ORANGE), 28)
        cv2.line(image, (x, y-11), (x+180, y-11), (YELLOW), 20)

        if distance < warning_threshold:
            # red distance bar
            cv2.line(image, (x, y-45), (x+100, y-45), (RED), 22)
            cv2.line(image, (x, y-11), (x+180, y-11), (RED), 18)
        else:
            cv2.line(image, (x, y-11),
                     (max(x, int(x+(120-distance_level)*180/(120-warning_threshold))), y-11),
                     (GREEN), 18)
            # cv2.line(image, (x, y-11), (x+180-distance_level, y-11), (GREEN), 18)

        face_center: Tuple[int, int] = (int(w/2)+x, int(h/2)+y)
        cv2.circle(image, face_center, 5, (MAGENTA), 1)
        cv2.putText(image, f'distance {distance} cm',
                    (x-6, y-6), font_3, 0.5, (BLACK), 2)

        if distance < warning_threshold:
            # warning messages
            cv2.putText(image, 'TOO NEAR!!', (x-3, y-40), font_2, 0.6, (WHITE), 1)
            cv2.putText(image, 'STAY FARTHER, PLEASE.', (0, 30), font_2, 1, (RED), 2)
        else:
            cv2.putText(image, 'PROPER DISTANCE', (0, 30), font_2, 1, (BLACK), 2)
