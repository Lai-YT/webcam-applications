import cv2
import matplotlib.pyplot as plt

from image_filter.filter import ImageFilter
from util.path import to_abs_path


if __name__ == "__main__":
    dir = to_abs_path("image_filter")
    ref_img = cv2.imread(dir + "/img/ref_img.jpg")
    image_1 = cv2.imread(dir + "/img/dark_room.jpg")
    image_2 = cv2.imread(dir + "/img/dark_room_with_lightspot.jpg")

    ImageFilter.refresh_image(ref_img)
    ImageFilter.plot_image()
