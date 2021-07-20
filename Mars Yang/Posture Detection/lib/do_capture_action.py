import cv2
from pathlib import Path

# Config settings
keyboard_spacebar = 32
training_dir = 'train'

def do_capture_action(action_n):
    img_count = 0
    output_folder = '{}/action_{:02}'.format(training_dir, action_n)
    print('Capturing samples for {} into folder {}'.format(action_n, output_folder))
    Path(output_folder).mkdir(parents=True, exist_ok=True)

    # Video capture stuff
    videocapture = cv2.VideoCapture(0)
    if not videocapture.isOpened():
        raise IOError('Cannot open webcam')

    while True:
        _, frame = videocapture.read()
        filename = '{}/{:08}.png'.format(output_folder, img_count)
        cv2.imwrite(filename, frame)
        img_count += 1
        key = cv2.waitKey(100)
        cv2.imshow('', frame)

        if key == keyboard_spacebar:
            break

    # Clean up
    videocapture.release()
    cv2.destroyAllWindows()