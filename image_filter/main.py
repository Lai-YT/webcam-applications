import cv2

from image_filter.tools import FilterMode, filter_image, plot_image
from util.path import to_abs_path


if __name__ == "__main__":

    # ref_img = cv2.cvtColor(cv2.imread(to_abs_path("ref_img.jpg")), cv2.COLOR_BGR2RGB)
    image_1 = cv2.cvtColor(cv2.imread(to_abs_path("image_filter/img/dark_room.jpg")), cv2.COLOR_BGR2RGB)
    image_2 = cv2.cvtColor(cv2.imread(to_abs_path("image_filter/img/dark_room_with_lightspot.jpg")), cv2.COLOR_BGR2RGB)

    # filter mode: MEAN, GAUSSIAN, BILATERAL
    images = filter_image(image_2, FilterMode.BILATERAL)
    plot_image(images)
