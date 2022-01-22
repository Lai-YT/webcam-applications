import cv2
import dlib
import imutils
import matplotlib.pyplot as plt
from imutils import face_utils
from nptyping import Int, NDArray

from image_filter.filter import ImageFilter, plot_mask_diff
from util.color import CYAN, MAGENTA
from util.cv_font import FONT_0
from util.image_type import ColorImage
from util.path import to_abs_path


detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor(
    "posture/trained_models/shape_predictor_68_face_landmarks.dat")
filter = ImageFilter()


def real_time_brightness_capture() -> None:
    cam = cv2.VideoCapture(0)

    while cam.isOpened():
        _, frame = cam.read()
        frame = cv2.flip(frame, flipCode=1)
        faces: dlib.rectangles = detector(frame)
        if len(faces) == 0:
            continue
        # 1st is used
        face: dlib.rectangle = faces[0]
        filter.refresh_image(frame, face)
        # draw face
        fx, fy, fw, fh = face_utils.rect_to_bb(faces[0])
        cv2.rectangle(frame, (fx, fy), (fx+fw, fy+fh), MAGENTA, 1)

        brightness: float = filter.get_brightness()
        cv2.putText(frame, f"Bright. = {brightness}", (50, 50), FONT_0, 1, CYAN, 2)
        frame = imutils.resize(frame, width=600)
        cv2.imshow("Brightness", frame)
        if cv2.waitKey(100) & 0xFF == ord("q"):
            break


def show_static_diff(frame: ColorImage) -> None:
    frame = cv2.flip(frame, flipCode=1)
    faces: dlib.rectangles = detector(frame)
    if len(faces) == 0:
        print("no face")
        return
    # 1st is used
    face: dlib.rectangle = faces[0]
    filter.refresh_image(frame, face)
    plot_mask_diff(filter)


if __name__ == "__main__":
    # real_time_brightness_capture()

    dir = to_abs_path("image_filter")
    frame = cv2.imread(dir + "/img/ref_img.jpg")
    show_static_diff(frame)
