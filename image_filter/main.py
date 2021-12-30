import cv2

from tools import filter_image, plot_image, Mode


if __name__ == '__main__':

    # ref_img = cv2.cvtColor(cv2.imread("ref_img.jpg"), cv2.COLOR_BGR2RGB)
    image_1 = cv2.cvtColor(cv2.imread("img/dark_room.jpg"), cv2.COLOR_BGR2RGB)
    image_2 = cv2.cvtColor(cv2.imread("img/dark_room_with_lightspot.jpg"), cv2.COLOR_BGR2RGB)

    # mode: MEAN, GAUSSIAN, BILATERAL
    images = filter_image(image_2, Mode.BILATERAL)
    plot_image(images)
