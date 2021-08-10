import cv2
import dlib
import os
from imutils import face_utils

from lib.color import MAGENTA, RED
from path import to_abs_path


predictor_path = to_abs_path('lib/trained_models/shape_predictor_68_face_landmarks.dat')

if __name__ == '__main__':
    detector = dlib.get_frontal_face_detector()
    predictor = dlib.shape_predictor(predictor_path)

    target_file = to_abs_path('lib/train_sample/gaze/good')
    for f in os.listdir(target_file):
        print(f'Processing file: {f}')
        img = cv2.imread(target_file + '\\' + f)
        img = cv2.flip(img, flipCode=1)
        canvas = img.copy()

        dets = detector(img)
        print(f'Number of faces detected: {len(dets)}')
        for d in dets:
            fx, fy, fw, fh = face_utils.rect_to_bb(d)
            cv2.rectangle(canvas, (fx, fy), (fx+fw, fy+fh), MAGENTA, 1)

            shape = predictor(img, d)
            shape = face_utils.shape_to_np(shape)
            for lx, ly in shape:
                cv2.circle(canvas, (lx, ly), 1, RED, -1)

        cv2.imshow('landmarks', canvas)
        if cv2.waitKey(300) == 27:
            break
