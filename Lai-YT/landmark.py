import cv2
import math

from lib.color import LIGHT_BLUE
from lib.cv_font import FONT_3
from lib.face_angle_detector import FaceAngleDetector
from lib.video_writer import VideoWriter
from path import to_abs_path


def main() -> None:
    angle_detector = FaceAngleDetector()

    video_writer = VideoWriter(to_abs_path('output/landmark'), fps=8.0)
    camera = cv2.VideoCapture(0)

    while camera.isOpened() and cv2.waitKey(1) != 27:
        _, frame = camera.read()

        # image captured by camera is mirrored
        frame = cv2.flip(frame, flipCode=1)
        canvas = frame.copy()

        angle_detector.refresh(frame)
        canvas = angle_detector.mark_facemarks(canvas)

        angles = angle_detector.angles()
        if angles:
            # only puts the angle of the first face
            cv2.putText(canvas, str(round(angles[0], 1)), (10, 30), FONT_3, 0.9, LIGHT_BLUE, 1)

        video_writer.write(canvas)
        cv2.imshow('facemark', canvas)

    video_writer.release()
    camera.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
