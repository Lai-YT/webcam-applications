"""
Visualized version of applications. No warning, detection only.
Specific design for alpha.py.
"""

import cv2
import numpy as np
from playsound import playsound
from typing import Optional

from .color import *
from .cv_font import *
from .face_distance_detector import FaceDetector, DistanceDetector
from .gaze_tracking import GazeTracking
from .timer import Timer
from .train import PostureMode, PostureLabel, image_dimensions

# type hints
Image = np.ndarray

def do_distance_measurement(frame: Image, distance_detector: DistanceDetector) -> Image:
    """Estimates the distance in the frame by FaceDistanceDetector.
    Returns the frame with distance text.

    Arguments:
        frame (numpy.ndarray): Imgae with face to be detected
        distance_detector (DistanceDetector): The detector used to estimate the distance
    """
    frame = frame.copy()
    distance: Optional[float] = distance_detector.distance()
    text: str = ""
    if distance is not None:
        distance = distance_detector.distance()
        text = "dist. " + str(int(distance))
    else:
        text = "No face detected."
    cv2.putText(frame, text, (10, 30), FONT_3, 0.9, MAGENTA, 1)

    return frame


def do_focus_time_record(frame: Image, timer: Timer,face: FaceDetector, gaze: GazeTracking) -> Image:
    """If there's face or eyes in the frame, the timer wil keep timing, otherwise stops.
    Returns the frame with time stamp.

    Arguments:
        frame (numpy.ndarray): The image to detect whether the user is gazing
        timer (Timer): The timer object that records the time
        face_detector (FaceDetector): Detect face in the frame
        gaze (GazeTracking): Detect eyes in the frame
    """
    frame = frame.copy()
    if not face.has_face and not gaze.pupils_located:
        timer.pause()
        cv2.putText(frame, "time pause", (510, 40), FONT_3, 0.6, RED, 1)
    else:
        timer.start()
    time_duration: str = f"t. {(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(frame, time_duration, (510, 20), FONT_3, 0.8, BLUE, 1)

    return frame


def do_posture_watch(frame: Image, mymodel, mode: PostureMode) -> Image:
    """Returns the frame with posture label text.

    Arguments:
        frame (numpy.ndarray): The image contains posture to be watched
        mymodel (tensorflow.keras.Model): To predict the label of frame
        mode (PostureMode): The mode will also be part of the text
    """
    im_color: Image = frame.copy()
    im: Image = cv2.cvtColor(im_color, cv2.COLOR_BGR2GRAY)

    im = cv2.resize(im, image_dimensions)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *image_dimensions, 1)

    predictions: np.ndarray = mymodel.predict(im)
    class_pred: np.int64 = np.argmax(predictions)
    conf: np.float32 = predictions[0][class_pred]

    im_color = cv2.resize(im_color, (640, 480), interpolation=cv2.INTER_AREA)

    if class_pred == PostureLabel.slump.value:
        im_color = cv2.putText(im_color, f'{mode.name}-slump', (10, 70), FONT_0, 1, RED, thickness=2)
    else:
        im_color = cv2.putText(im_color, f'{mode.name}-good', (10, 70), FONT_0, 1, GREEN, thickness=2)

    msg: str = f'confidence {round(int(conf*100))}%'
    im_color = cv2.putText(im_color, msg, (15, 110), FONT_0, 0.6, (200, 200, 255), thickness=2)
    return im_color
