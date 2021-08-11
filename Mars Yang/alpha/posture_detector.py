# tutorial to refer to:
# https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/

import cv2
import dlib
import math

import warnings
from imutils import face_utils

from lib.color import GREEN, RED
from lib.cv_font import *
from lib.video_writer import VideoWriter
from numpy import *
from path import to_abs_path


# For dlib’s 68-point facial landmark detector
NOSE_BRIDGE_IDXS = [27, 30]
LEFT_EYESIDE_IDXS = [36, 39]
RIGHT_EYESIDE_IDXS = [42, 45]
MOUTHSIDE_IDXS = [48, 54]


def angle(p1, p2) -> float:
    """Returns the included angle of the vector (x2 - x1, y2 - y1) in degree."""
    x1 ,y1 = p1
    x2 ,y2 = p2
    with warnings.catch_warnings():
        # RuntimeWarning: divide by zero encountered in long_scalars
        # Ignore possible warning when 90.0
        warnings.simplefilter("ignore", category=RuntimeWarning)
        return math.atan((y2 - y1) / (x2 - x1)) * 180 / math.pi


def posture_detect(frame, detector, predictor) -> None:
    dets = detector(frame)
    # put a warning text if no face detected
    if len(dets) == 0:
        cv2.putText(frame, "No face detected.", (10, 30), FONT_3, 0.9, RED, 1)
    
    for d in dets:
        ''' Determine the facial landmarks for the face region, then
	        convert the facial landmark (x, y)-coordinates to a NumPy
	        array.
        '''
        shape = predictor(frame, d)
        shape = face_utils.shape_to_np(shape)

        # slope angles of all parts in face
        nose_angle = angle(shape[NOSE_BRIDGE_IDXS[0]], shape[NOSE_BRIDGE_IDXS[1]])
        right_eye_angle = angle(shape[RIGHT_EYESIDE_IDXS[0]], shape[RIGHT_EYESIDE_IDXS[1]])
        left_eye_angle = angle(shape[LEFT_EYESIDE_IDXS[0]], shape[LEFT_EYESIDE_IDXS[1]])
        mouth_angle = angle(shape[MOUTHSIDE_IDXS[0]], shape[MOUTHSIDE_IDXS[1]])

        slope_angle = round(((90 - abs(nose_angle)) + abs(right_eye_angle) + 
                             abs(left_eye_angle) + abs(mouth_angle)) / 4, 1) # average slope angle

        # if slope angle < 10, good; else, slump
        text, color = (("Good", GREEN) if (slope_angle < 10) else ("Slump", RED))

        cv2.putText(frame, text, (10, 30), FONT_3, 0.9, color, 1)
        cv2.putText(frame, f'Slope Angle: {slope_angle} degrees', (10, 60), FONT_3, 0.7, color, 1)

def main() -> None:
    '''The former process of posture detection.'''
    predictor_path = to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat')

    # Initialize dlib's face detector (HOG-based) and then create
    # the facial landmark predictor.
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    video_writer = VideoWriter(to_abs_path('landmark'), fps=10.0)
    camera = cv2.VideoCapture(0)

    while camera.isOpened() and cv2.waitKey(1) != 27:
        _, frame = camera.read()
        frame = cv2.flip(frame, flipCode=1)

        # main process: posture detection
        posture_detect(frame, detector, predictor)

        video_writer.write(frame)
        cv2.imshow('facemark', frame)

    video_writer.release()
    camera.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()
