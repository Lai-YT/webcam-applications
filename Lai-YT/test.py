import cv2
from typing import List

from lib.color import BLUE, GREEN, RED, WHITE
from lib.cv_font import FONT_1
from lib.face_distance_detector import FaceDetector
from lib.image_type import ColorImage


if __name__ == "__main__":
    images: List[ColorImage] = []

    for i in range(40):
        images.append(cv2.imread(f"lib/train_sample/gaze/good/{i:08d}.jpg"))

    for image in images:
        canvas: ColorImage = image.copy()
        print("x, y, w, h:")
        x, y, w, h = FaceDetector.face_data(image)[0]
        cv2.rectangle(canvas, (x, y), (x + w, y + h), GREEN, 2)
        cv2.putText(canvas, 'cv2', (x, y), FONT_1, 1, WHITE, 1)
        print('cv2:', x, y, w, h)

        x, y, w, h = FaceDetector.face_data_rec(image)[0]
        cv2.rectangle(canvas, (x, y), (x + w, y + h), BLUE, 2)
        cv2.putText(canvas, 'rec', (x, y), FONT_1, 1, WHITE, 1)
        print('rec:', x, y, w, h)

        x, y, w, h = FaceDetector.face_data_dlib(image)[0]
        cv2.rectangle(canvas, (x, y), (x + w, y + h), RED, 2)
        cv2.putText(canvas, 'dlib', (x, y), FONT_1, 1, WHITE, 1)
        print('dli:', x, y, w, h)

        cv2.imshow('face', canvas)
        if cv2.waitKey(500) == 27:  # esc
            break

    cv2.destroyAllWindows()
