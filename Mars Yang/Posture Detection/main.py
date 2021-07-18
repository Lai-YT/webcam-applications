import argparse

from lib.do_capture_action import *
from lib.do_training import *
from lib.do_live_view import *

def main():
    parser = argparse.ArgumentParser(description='Posture monitor')
    parser.add_argument('--capture-good', help='capture example of good, healthy posture', action='store_true')
    parser.add_argument('--capture-slump', help='capture example of poor, slumped posture', action='store_true')
    parser.add_argument('--train', help='train model with captured images', action='store_true')
    parser.add_argument('--live', help='live view applying model to each frame', action='store_true')
    parser.add_argument('--sound', help='in conjunction with live view will make a sound', action='store_true')
    args = parser.parse_args()

    if args.train:
        do_training()
    elif args.live:
        do_live_view(args.sound)
    elif args.capture_good:
        do_capture_action(1, 'Good')
    elif args.capture_slump:
        do_capture_action(2, 'Slumped')
    else:
        parser.print_help()

if __name__ == '__main__':
    main()