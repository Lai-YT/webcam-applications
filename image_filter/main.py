import cv2
import matplotlib.pyplot as plt

from image_filter.face_detector import detect_and_mark_face
from image_filter.mask import get_brightness
from util.path import to_abs_path


def plot(image):
    title = f"Brightness before masked: {get_brightness(image, mask=False)}\nBrightness after masked: {get_brightness(image, mask=True)}"

    plt.imshow(image)
    plt.title(title)
    plt.show()

if __name__ == "__main__":

    ref_img = cv2.imread(to_abs_path("image_filter/img/ref_img.jpg"))
    # image_1 = cv2.imread(to_abs_path("image_filter/img/dark_room.jpg"))
    # image_2 = cv2.imread(to_abs_path("image_filter/img/dark_room_with_lightspot.jpg"))
    # image_3 = cv2.imread(to_abs_path("image_filter/img/dark_room_with_lightspot1.jpg"))

    frame = detect_and_mark_face(ref_img)
    plot(frame)
