import cv2
from numpy import ndarray

from lib.distance import *

'''
variables (should be set by the user)
'''
# distance from camera to object(face) measured
known_distance: float = 45  # centi-meter
# mine is 14.3 something, measure your face width, or google it
known_width: float = 12.5  # centi-meter
# a reference image of your face for calculating the distance
ref_image_path = 'distance_measurement/img/ref_img.jpg'
# To show the distance bar or not.
call_out: bool = True
# warns when the distance is shorter than threshold
warning: int = 45  # centi-meter


'''
getting informations from reference image
'''
ref_image: ndarray = cv2.imread(ref_image_path)
ref_image_face_width: int = 0
for (_, _, w, _) in face_data(ref_image):
    ref_image_face_width = w
focal_length_found = focal_length(
    known_distance, ref_image_face_width, known_width)


if __name__ == '__main__':
    # Camera Object
    cap = cv2.VideoCapture(0)  # Number According to your Camera

    # Define the codec and create VideoWriter object
    # fourcc: int = cv2.VideoWriter_fourcc(*'XVID')
    # out = cv2.VideoWriter('face_distance.avi', fourcc, 30.0, (640, 480))
    while True:
        _, frame = cap.read()

        faces: ndarray = face_data(frame)  # type: ndarray[int, int, int, int]

        # finding the distance by calling function distance finder
        for (face_x, face_y, face_w, face_h) in faces:
            if face_w != 0:
                draw_face_area(frame, faces)
                if call_out:
                    distance: float = distance_finder(
                        focal_length_found, known_width, face_w)
                    show_distance_bar(
                        frame, faces, distance, warning_threshold=warning)

        cv2.imshow('frame', frame)
        # out.write(frame)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    # out.release()
    cv2.destroyAllWindows()
