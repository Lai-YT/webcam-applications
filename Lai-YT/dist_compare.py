import cv2
import dlib
from imutils import face_utils
from math import sqrt

from lib.color import GREEN, LIGHT_BLUE
from lib.cv_font import FONT_0
from lib.distance_detector import DistanceDetector
from lib.video_writer import VideoWriter
from path import to_abs_path


PREDICTOR_PATH = to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat')
FACE_WIDTH = 45.0
CAMERA_DIST = 11.5


def get_face_width(shape) -> float:
    shape = face_utils.shape_to_np(shape)
    # zygomatic bones
    p1 = shape[1]
    p2 = shape[15]
    return euclidean_distance(p1, p2)


def euclidean_distance(p1, p2) -> float:
    x1, y1 = p1
    x2, y2 = p2
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


if __name__ == '__main__':
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(PREDICTOR_PATH)

    # parameters (FACE_WIDTH_IN_REF, FOCAL):
    # needed when evaluating distance
    ref_img = cv2.imread(to_abs_path('img/ref_img.jpg'))
    face = detector(ref_img)
    shape = predictor(ref_img, face[0])

    # 1
    FACE_WIDTH_IN_REF = get_face_width(shape)
    FOCAL = (FACE_WIDTH_IN_REF * CAMERA_DIST) / FACE_WIDTH
    # 2
    dist_detector = DistanceDetector(ref_img, FACE_WIDTH, CAMERA_DIST)

    video_writer = VideoWriter(to_abs_path('output/distance'), fps=8.0)
    camera = cv2.VideoCapture(0)
    while camera.isOpened() and cv2.waitKey(10) != 27:
        _, frame = camera.read()

        frame = cv2.flip(frame, flipCode=1)
        canvas = frame.copy()

        # 1
        faces = detector(frame)
        if len(faces) != 0:
            face = faces[0]
            shape = predictor(frame, face)

            i, j = face_utils.FACIAL_LANDMARKS_IDXS['jaw']
            for lx, ly in face_utils.shape_to_np(shape)[i:j]:
                cv2.circle(canvas, (lx, ly), 2, GREEN, -1)

            face_dist = (FACE_WIDTH_IN_REF * FOCAL) / get_face_width(shape)
            text = f'dlib: {face_dist:2.1f}'
        else:
            text = 'dlib: x'
        cv2.putText(canvas, text, (10, 30), FONT_0, 0.9, LIGHT_BLUE, 2)

        # 2
        dist_detector.estimate(frame)
        face_dist = dist_detector.distance()
        if face_dist is not None:
            text = f'cv2: {face_dist:2.1f}'
        else:
            text = 'cv2: x'
        cv2.putText(canvas, text, (10, 70), FONT_0, 0.9, LIGHT_BLUE, 2)
        
        video_writer.write(canvas)
        cv2.imshow('landmarks', canvas)

    camera.release()
    cv2.destroyAllWindows()
