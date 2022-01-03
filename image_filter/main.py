import cv2
import matplotlib.pyplot as plt

from image_filter.mask import get_brightness
from util.path import to_abs_path


def plot(image):
    title = f"Brightness before masked: {get_brightness(image, masking=False)}\nBrightness after masked: {get_brightness(image, masking=True)}"

    plt.imshow(image)
    plt.title(title)
    plt.show()

if __name__ == "__main__":

    # ref_img = cv2.cvtColor(cv2.imread(to_abs_path("ref_img.jpg")), cv2.COLOR_BGR2RGB)
    image_1 = cv2.cvtColor(cv2.imread(to_abs_path("image_filter/img/dark_room.jpg")), cv2.COLOR_BGR2RGB)
    image_2 = cv2.cvtColor(cv2.imread(to_abs_path("image_filter/img/dark_room_with_lightspot.jpg")), cv2.COLOR_BGR2RGB)
    image_3 = cv2.cvtColor(cv2.imread(to_abs_path("image_filter/img/dark_room_with_lightspot1.jpg")), cv2.COLOR_BGR2RGB)

    plot(image_2)
    plot(image_3)
