import argparse

from lib.train import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Capture images and train the model before using the functon of posture watching (in demo.py and alpha.py).')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-gg', '--capture-gaze-good', help='capture sample images of good, healthy posture when gazing the screen', action='store_true')
    group.add_argument('-gs', '--capture-gaze-slump', help='capture sample images of poor, slumped posture when gazing the screen', action='store_true')
    group.add_argument('-wg', '--capture-write-good', help='capture sample images of good, healthy posture when writing in front of the screen', action='store_true')
    group.add_argument('-ws', '--capture-write-slump', help='capture sample images of poor, slumped posture when writing in front of the screen', action='store_true')
    group.add_argument('-t', '--train', help='train model with captured images', action='store_true')
    group.add_argument('-r', '--reset', help='remove sample images before starting a new series of capture', action='store_true')
    args = parser.parse_args()

    if args.train:
        train_model()
    elif args.capture_gaze_good:
        capture_action(PostureMode.gaze, PostureLabel.good)
    elif args.capture_gaze_slump:
        capture_action(PostureMode.gaze, PostureLabel.slump)
    elif args.capture_write_good:
        capture_action(PostureMode.write, PostureLabel.good)
    elif args.capture_write_slump:
        capture_action(PostureMode.write, PostureLabel.slump)
    elif args.reset:
        remove_sample_images()
    else:
        parser.print_help()
