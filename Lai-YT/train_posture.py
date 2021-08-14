import argparse

from lib.train import PostureLabel, capture_writing_action, remove_sample_images, train_writing_model


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Capture images and train the model before using the functon of posture watching (in demo.py and alpha.py).')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-cg', '--capture-good', help='capture sample images of good, healthy posture when writing in front of the screen', action='store_true')
    group.add_argument('-cs', '--capture-slump', help='capture sample images of poor, slumped posture when writing in front of the screen', action='store_true')
    group.add_argument('-t', '--train', help='train model with captured images', action='store_true')
    group.add_argument('-r', '--reset', help='remove sample images before starting a new series of capture', action='store_true')
    args = parser.parse_args()

    if args.train:
        train_writing_model()
    elif args.capture_good:
        capture_writing_action(PostureLabel.good)
    elif args.capture_slump:
        capture_writing_action(PostureLabel.slump)
    elif args.reset:
        remove_sample_images()
    else:
        parser.print_help()
