import cv2
from typing import List

from lib.face_distance_detector import FaceDetector
from lib.image_type import ColorImage


if __name__ == "__main__":
    images: List[ColorImage] = []

    for i in range(40):
        images.append(cv2.imread(f"lib/train_sample/gaze/good/{i:08d}.jpg"))

    for image in images:
        print("x, y, w, h:")
        x, y, w, h = FaceDetector.face_data(image)[0]
        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
        print('cv2:', x, y, w, h)

        x, y, w, h = FaceDetector.face_data_2(image)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        print('rec:', x, y, w, h)

        cv2.imshow('face', image)
        if cv2.waitKey(500) == 27:  # esc
            break

    cv2.destroyAllWindows()
