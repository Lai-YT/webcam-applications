import cv2
import screen_brightness_control as sbc


def control_brightness():
    # resource: https://pypi.org/project/screen-brightness-control/

    # laptop screen
    method = 'wmi'

    # 1. Print the current brightness of computer.
    print(f'The current brightness of the computer is {sbc.get_brightness(method=method)}.')
    # 2. Set the brightness of computer to 7%.
    sbc.set_brightness(8, method=method)
    # 3. Print the current brightness of computer again.
    #    should be 7%.
    #print(f'The current brightness of the computer is {sbc.get_brightness(method=method)}.')
    # 4. Set the brightness of computer to 10 and fade to 0.
    #sbc.fade_brightness(0, start=10, interval=0.1)


def get_brightness_of_frame():
    """Gets frame from camera and shows the value part of it."""
    cam = cv2.VideoCapture(0)
    while True:
        _, frame = cam.read()
        print(get_information(frame))

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        h, s, v = cv2.split(hsv)
        cv2.imshow('value', v)
        if cv2.waitKey(0) == 27:
            break


def get_brightness_of_image():
    # This is a pure white image.
    white = cv2.imread('img/white.jpg')
    print('white(pure):')
    print('\t' + get_information(white))

    # This is dark but not totally black image.
    black = cv2.imread('img/black.jpg')
    print('black(not pure):')
    print('\t' + get_information(black))


def get_information(image):
    """Returns mean, standard deviation and variance of the brightness in str."""
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # hue, saturation, value
    # Value is as known as brightness.
    h, s, v = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
    return f'mean = {v.mean():.2f}({v.mean() / 255:.2%}), std = {v.std():.2f}, var = {v.var():.2f}'


if __name__ == '__main__':
    import time

    print('This demo contains 3 parts.')
    print('The first part shows how to control the brightness of screen(Windows).')
    time.sleep(2)
    control_brightness()
    print()

    print('The second part shows how to get the brightness of an image.')
    time.sleep(2)
    get_brightness_of_image()
    print()

    print('The last part shows the live version of the second part.')
    print('This opens the webcam and starts a loop, do you want to continue? Y/N: ', end='')
    if input().lower() == 'y':
        print('Try adjusting the light of your room to see the change in brightness.')
        print('You may press \'esc\' to end the loop.')
        get_brightness_of_frame()
    print('End.')
