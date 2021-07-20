import argparse

from lib.posture import *
from path import to_abs_path


model_path: str = to_abs_path('lib/trained_models/posture_model.h5')
training_dir: str = to_abs_path('train')
mp3file: str = to_abs_path('sounds/what.mp3')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Posture monitor')
    parser.add_argument('-cg', '--capture-good', help='capture example of good, healthy posture', action='store_true')
    parser.add_argument('-cs', '--capture-slump', help='capture example of poor, slumped posture', action='store_true')
    parser.add_argument('-t', '--train', help='train model with captured images', action='store_true')
    parser.add_argument('-l', '--live', help='live view applying model to each frame', action='store_true')
    parser.add_argument('-s', '--sound', help='in conjunction with live view will make a sound', action='store_true')
    args = parser.parse_args()

    if args.train:
        do_training(training_dir, model_path)
    elif args.live:
        do_live_view(model_path, args.sound, mp3file)
    elif args.capture_good:
        do_capture_action(1, 'Good')
    elif args.capture_slump:
        do_capture_action(2, 'Slumped')
    else:
        parser.print_help()
