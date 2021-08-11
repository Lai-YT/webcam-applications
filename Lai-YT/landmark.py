# tutorial to refer to:
# https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/

import cv2
import dlib
import math
import os
import warnings
from imutils import face_utils

from lib.color import GREEN, MAGENTA, RED
from lib.video_writer import VideoWriter
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


def main() -> None:
    predictor_path = to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat')

    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    video_writer = VideoWriter(to_abs_path('output/landmark'), fps=8.0)
    camera = cv2.VideoCapture(0)

    while camera.isOpened() and cv2.waitKey(1) != 27:
        _, frame = camera.read()

        # image captured by camera is mirrored
        frame = cv2.flip(frame, flipCode=1)
        canvas = frame.copy()

        faces = detector(frame)
        for face in faces:
        	# to the format (x, y, w, h) as we would normally do with OpenCV
            fx, fy, fw, fh = face_utils.rect_to_bb(face)
            cv2.rectangle(canvas, (fx, fy), (fx+fw, fy+fh), MAGENTA, 2)

            shape = predictor(frame, face)
            # converts to a 2-tuple of (x, y)-coordinates
            shape = face_utils.shape_to_np(shape)
            # if the face skews over 10 degrees, color of lines is set to red
            color = (GREEN
                if (abs(angle(shape[NOSE_BRIDGE_IDXS[0]], shape[NOSE_BRIDGE_IDXS[1]])) > 80
                    and abs(angle(shape[RIGHT_EYESIDE_IDXS[0]], shape[RIGHT_EYESIDE_IDXS[1]])) < 10
                    and abs(angle(shape[LEFT_EYESIDE_IDXS[0]], shape[LEFT_EYESIDE_IDXS[1]])) < 10
                    and abs(angle(shape[MOUTHSIDE_IDXS[0]], shape[MOUTHSIDE_IDXS[1]])) < 10)
                else RED
            )
            cv2.line(
                canvas,
                shape[LEFT_EYESIDE_IDXS[0]], shape[LEFT_EYESIDE_IDXS[1]],
                color, 2, cv2.LINE_AA
            )
            cv2.line(
                canvas,
                shape[RIGHT_EYESIDE_IDXS[0]], shape[RIGHT_EYESIDE_IDXS[1]],
                color, 2, cv2.LINE_AA
            )
            cv2.line(
                canvas,
                shape[NOSE_BRIDGE_IDXS[0]], shape[NOSE_BRIDGE_IDXS[1]],
                color, 2, cv2.LINE_AA
            )
            cv2.line(
                canvas,
                shape[MOUTHSIDE_IDXS[0]], shape[MOUTHSIDE_IDXS[1]],
                color, 2, cv2.LINE_AA
            )
        # make lines transparent
        canvas = cv2.addWeighted(canvas, 0.4, frame, 0.6, 0)

        video_writer.write(canvas)
        cv2.imshow('facemark', canvas)

    video_writer.release()
    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
