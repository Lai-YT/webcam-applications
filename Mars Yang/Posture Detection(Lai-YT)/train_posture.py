import argparse

from lib.app import capture_action, train


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Capture images and train the model before using the functon of posture watching (demo.py and real.py).')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-cg', '--capture-good', help='capture example of good, healthy posture', action='store_true')
    group.add_argument('-cs', '--capture-slump', help='capture example of poor, slumped posture', action='store_true')
    group.add_argument('-t', '--train', help='train model with captured images', action='store_true')
    args = parser.parse_args()

    if args.train:
        train()
    elif args.capture_good:
        capture_action(1, 'good')
    elif args.capture_slump:
        capture_action(2, 'slump')
    else:
        parser.print_help()
