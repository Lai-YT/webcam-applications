import argparse

from lib.train import *


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Capture images and train the model before using the functon of posture watching (in demo.py and alpha.py).')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-g', '--capture-gaze', help='capture sample images of postures when gazing the screen', action='store_true')
    group.add_argument('-w', '--capture-write', help='capture sample images of postures when writing in front of the screen', action='store_true')
    group.add_argument('-s', '--capture-slump', help='capture sample images of poor, slumped posture in front of the screen', action='store_true')
    group.add_argument('-t', '--train', help='train model with captured images', action='store_true')
    group.add_argument('-r', '--reset', help='remove sample images before starting a new series of capture', action='store_true')
    args = parser.parse_args()

    if args.train:
        train_model()
    elif args.capture_gaze:
        capture_action('gaze')
    elif args.capture_write:
        capture_action('write')
    elif args.capture_slump:
        capture_action('slump')
    elif args.reset:
        remove_sample_images()
    else:
        parser.print_help()
