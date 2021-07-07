import cv2
from numpy import ndarray
from typing import Tuple

from .color import *


# focal length finder function
def focal_length(measured_distance: float,
                 real_width: float,
                 width_in_rf_image: float) -> float:
    '''This function Calculate the focal length(distance between lens to CMOS sensor).
    @param
      measured_distance:
        distance measured from object to the Camera while Capturing Reference image
      real_width:
        Actual width of object, in real world (like My face width is = 5.7 Inches)
      width_in_rf_image:
        object width in the frame /image in our case in the reference image(found by Face detector)
    @retrun
        focal_length
    '''
    focal_length: float = (width_in_rf_image * measured_distance) / real_width
    return focal_length


# distance estimation function
def distance_finder(focal_length: float,
                    real_face_width: float,
                    face_width_in_frame: float) -> float:
    '''This Function simply Estimates the distance between object and camera.
    @param
      focal_length:
        may be the result of the focal_length function
      real_face_width:
        Actual width of object, in real world (like My face width is = 5.7 Inches)
      face_width_in_frame:
        width of object in the image(frame in our case, using Video feed)
    @return
        estimated distance
    '''
    distance = (real_face_width * focal_length) / face_width_in_frame
    return distance


# face detection Fauction
def face_data(image: ndarray,
              call_out: bool,
              distance_level: int) -> Tuple[int, Tuple[int, int, int, int], Tuple[int, int]]:
    '''This function Detect Face and Draw Rectangle and display the distance over Screen.
    @param
      image:
        simply the frame
      call_out:
        whether to show distance and Rectangle on the Screen or not
      distance_level:
        which change the line according the distance changes(Intractivate)
    @return
      face_width:
        width of face in the frame, which allow us to calculate the distance and
        find focal length
      face:
        length of face and (face paramters)
      face_center:
        face centroid_x coordinate(x) and face centroid_y coordinate(y)
    '''

    # face detector object
    face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    gray_image: ndarray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    faces: Tuple[int, int, int, int] = (
        face_detector.detectMultiScale(gray_image, 1.3, 5))
    face_width: int = 0
    face_center: Tuple[int, int] = None

    for (x, y, h, w) in faces:
        line_thickness: int = 2
        # print(len(faces))
        LLV = int(h*0.12)
        # print(LLV)

        # cv2.rectangle(image, (x, y), (x+w, y+h), BLACK, 1)
        cv2.line(image, (x, y+LLV), (x+w, y+LLV), (GREEN), line_thickness)
        cv2.line(image, (x, y+h), (x+w, y+h), (GREEN), line_thickness)
        cv2.line(image, (x, y+LLV), (x, y+LLV+LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w, y+LLV), (x+w, y+LLV+LLV),
                 (GREEN), line_thickness)
        cv2.line(image, (x, y+h), (x, y+h-LLV), (GREEN), line_thickness)
        cv2.line(image, (x+w, y+h), (x+w, y+h-LLV), (GREEN), line_thickness)

        face_width = w
        # Drwaing circle at the center of the face
        face_center = (int(w/2)+x, int(h/2)+y)
        if distance_level < 10:
            distance_level = 10

        # cv2.circle(image, face_center, 5, (255,0,255), 3)
        if call_out == True:
            # cv2.line(image, (x,y), face_center, (155,155,155),1)
            cv2.line(image, (x, y-11), (x+180, y-11), (ORANGE), 28)
            cv2.line(image, (x, y-11), (x+180, y-11), (YELLOW), 20)
            cv2.line(image, (x, y-11), (x+distance_level, y-11), (GREEN), 18)

            cv2.circle(image, face_center, 2, (255,0,255), 1 )
            cv2.circle(image, (x, y), 2, (255,0,255), 1 )

    return face_width, faces, face_center
