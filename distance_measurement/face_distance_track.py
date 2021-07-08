import cv2
from numpy import ndarray

from lib.color import *
from lib.distance import *


# variables

# distance from camera to object(face) measured
known_distance: float = 45  # centi-meter
# mine is 14.3 something, measure your face width, or google it
known_width: float = 12.5  # centi-meter

# font_*, * is the corresponding enum number in the library
font_3: int = cv2.FONT_HERSHEY_COMPLEX
font_4: int = cv2.FONT_HERSHEY_TRIPLEX
font_5: int = cv2.FONT_HERSHEY_COMPLEX_SMALL
font_6: int = cv2.FONT_HERSHEY_SCRIPT_SIMPLEX

# Camera Object
cap = cv2.VideoCapture(0)  # Number According to your Camera
distance_level: int = 0

# Define the codec and create VideoWriter object
# fourcc: int = cv2.VideoWriter_fourcc(*'XVID')
# out = cv2.VideoWriter('face_distance.avi', fourcc, 30.0, (640, 480))

# reading reference image from directory
ref_image: ndarray = cv2.imread('distance_measurement/img/ref_img.jpg')

ref_image_face_width, _, _ = face_data(ref_image)
focal_length_found = focal_length(
    known_distance, ref_image_face_width, known_width)
# print(focal_length_found)
#
# cv2.imshow('ref_image', ref_image)


while True:
    _, frame = cap.read()
    # calling face_data function
    # distance_leve =0

    face_width_in_frame, faces, face_center = face_data(frame)

    # finding the distance by calling function distance finder
    for (face_x, face_y, face_w, face_h) in faces:
        if face_width_in_frame != 0:
            distance = distance_finder(
                focal_length_found, known_width, face_width_in_frame)
            distance = round(distance, 2)
            # Drwaing Text on the screen
            distance_level = int(distance)

            draw_face_area(frame, faces, distance_level, call_out=True)
            cv2.putText(frame, f'distance {distance} cm',
                        (face_x-6, face_y-6), font_3, 0.5, (BLACK), 2)
    cv2.imshow('frame', frame)
    # out.write(frame)

    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
# out.release()
cv2.destroyAllWindows()
