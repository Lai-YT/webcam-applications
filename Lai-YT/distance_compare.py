import cv2
import dlib
from imutils import face_utils

from lib.color import GREEN, LIGHT_BLUE
from lib.cv_font import FONT_0
from lib.distance_calculator import DistanceCalculator
from lib.video_writer import VideoWriter
from path import to_abs_path


PREDICTOR_PATH = to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat')
CAMERA_DIST = 45.0
FACE_WIDTH = 11.5


if __name__ == '__main__':
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(PREDICTOR_PATH)

    # initialize the calculator
    ref_img = cv2.imread(to_abs_path('img/ref_img.jpg'))
    face = detector(ref_img)
    landmarks = face_utils.shape_to_np(predictor(ref_img, face[0]))
    distance_calculator = DistanceCalculator(landmarks, CAMERA_DIST, FACE_WIDTH)

    # erase the context from the previous comparison
    open(to_abs_path('output/distance_compare.txt' as 'w')).close()

    video_writer = VideoWriter(to_abs_path('output/distance'), fps=8.0)
    camera = cv2.VideoCapture(0)
    while camera.isOpened() and cv2.waitKey(10) != 27:
        _, frame = camera.read()

        frame = cv2.flip(frame, flipCode=1)
        canvas = frame.copy()

        faces = detector(frame)
        if len(faces):
            has_face = True
            landmarks = face_utils.shape_to_np(predictor(frame, faces[0]))
        else:
            has_face = False
        if has_face:
            """draw landmarks"""
            # face
            cv2.line(canvas, landmarks[1], landmarks[15], GREEN, 2, cv2.LINE_AA)
            # nose
            cv2.line(canvas, landmarks[27], landmarks[30], GREEN, 2, cv2.LINE_AA)
            # make lines transparent
            canvas = cv2.addWeighted(canvas, 0.4, frame, 0.6, 0)

            """compare in the window"""
            by_face_width = round(distance_calculator.calculate_by_single_width(landmarks), 2)
            by_nose_height = round(distance_calculator.calculate_by_single_height(landmarks), 2)

            cv2.putText(canvas, f'face: {by_face_width}', (10, 30), FONT_0, 0.9, LIGHT_BLUE, 2)
            cv2.putText(canvas, f'nose: {by_nose_height}', (10, 70), FONT_0, 0.9, LIGHT_BLUE, 2)
            cv2.putText(canvas, f'ratio: {by_face_width / by_nose_height:.2%}', (10, 110), FONT_0, 0.9, LIGHT_BLUE, 2)

            """output to file"""
            with open(to_abs_path('output/distance_compare.txt'), 'a') as f:
                f.write(f'face: {by_face_width}\n')
                f.write(f'nose: {by_nose_height}\n')
                f.write(f'ratio: {by_face_width / by_nose_height:.2%}\n')
                f.write('---\n')

        video_writer.write(canvas)
        cv2.imshow('landmarks', canvas)

    camera.release()
    cv2.destroyAllWindows()
