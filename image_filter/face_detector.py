import cv2
import dlib
from imutils import face_utils

from util.color import MAGENTA
from util.image_type import ColorImage


def detect_and_mark_face(frame: ColorImage) -> ColorImage:
    """Detects face in a frame and mark it with rectangle."""
    face_detector = dlib.get_frontal_face_detector()

    faces: dlib.rectangles = face_detector(frame)
    # doesn't handle multiple faces
    if len(faces) == 1:
        fx, fy, fw, fh = face_utils.rect_to_bb(faces[0])
        cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), MAGENTA, 1)

    return frame
