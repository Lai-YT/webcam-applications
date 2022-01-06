import cv2
import matplotlib.pyplot as plt

from image_filter.face_detector import detect_and_mark_face
from image_filter.mask import get_brightness
from util.image_type import ColorImage
from util.path import to_abs_path


def plot(image: ColorImage) -> None:
    title = (f"Brightness before masked: {get_brightness(image, mask=False)}\n"
             f"Brightness after masked: {get_brightness(image, mask=True)}")

    plt.imshow(image)
    plt.title(title)
    plt.show()


if __name__ == "__main__":
    dir = to_abs_path("image_filter")
    ref_img = cv2.cvtColor(cv2.imread(dir + "/img/ref_img.jpg"), cv2.COLOR_BGR2RGB)
    image_1 = cv2.cvtColor(cv2.imread(dir + "/img/dark_room.jpg"), cv2.COLOR_BGR2RGB)
    image_2 = cv2.cvtColor(cv2.imread(dir + "/img/dark_room_with_lightspot.jpg"), cv2.COLOR_BGR2RGB)

    frame = detect_and_mark_face(ref_img)
    plot(frame)

    frame = detect_and_mark_face(image_1)
    plot(frame)

    frame = detect_and_mark_face(image_2)
    plot(frame)
