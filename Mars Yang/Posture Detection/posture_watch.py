import argparse

from lib.reset_training_folder import *
from lib.do_capture_action import *
from lib.do_training import *
from lib.do_live_view import *

def main():
    parser = argparse.ArgumentParser(description='Posture monitor')
    parser.add_argument('--capture-good', help='capture example of good, healthy posture', action='store_true')
    parser.add_argument('--capture-slump', help='capture example of poor, slumped posture', action='store_true')
    parser.add_argument('--reset', help='reset the training folder', action='store_true')
    parser.add_argument('--train', help='train model with captured images', action='store_true')
    parser.add_argument('--live', help='live view applying model to each frame', action='store_true')
    parser.add_argument('--sound', help='in conjunction with live view will make a sound', action='store_true')
    args = parser.parse_args()

    if args.train:
        # python posture_watch.py --train
        do_training()
    elif args.live:
        # python posture_watch.py --live (--sound)
        do_live_view(args.sound)
    elif args.capture_good:
        # python posture_watch.py --capture-good
        do_capture_action(1)
    elif args.capture_slump:
        # python posture_watch.py --capture-slump
        do_capture_action(2)
    elif args.reset:
        # python posture_watch.py --reset
        reset_training_folder()
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
