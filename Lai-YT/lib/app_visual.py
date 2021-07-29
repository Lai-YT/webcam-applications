"""
Visualized version of applications. No warning, detection only.
Specific design for alpha.py.
"""

import cv2
import numpy as np
from playsound import playsound
from nptyping import Float, Int, NDArray
from typing import Any, Optional

from .color import *
from .cv_font import *
from .face_distance_detector import DistanceDetector, FaceDetector
from .gaze_tracking import GazeTracking
from .image_type import ColorImage, GrayImage
from .timer import Timer
from .train import PostureMode, PostureLabel, image_dimensions


def do_distance_measurement(frame: ColorImage, distance_detector: DistanceDetector) -> ColorImage:
    """Estimates the distance in the frame by FaceDistanceDetector.
    Returns the frame with distance text.

    Arguments:
        frame (NDArray[(Any, Any, 3), UInt8]): Imgae with face to be detected
        distance_detector (DistanceDetector): The detector used to estimate the distance
    """
    frame = frame.copy()
    distance: Optional[float] = distance_detector.distance()
    text: str = ""
    if distance is not None:
        distance = distance_detector.distance()
        text = "dist. " + str(round(distance, 2))
    else:
        text = "No face detected."
    cv2.putText(frame, text, (60, 30), FONT_3, 0.9, MAGENTA, 1)

    return frame


def do_focus_time_record(frame: ColorImage, timer: Timer, face_detector: FaceDetector, gaze: GazeTracking) -> ColorImage:
    """If there's face or eyes in the frame, the timer wil keep timing, otherwise stops.
    Returns the frame with time stamp.

    Arguments:
        frame (NDArray[(Any, Any, 3), UInt8]): The image to detect whether the user is gazing
        timer (Timer): The timer object that records the time
        face_detector (FaceDetector): Detect face in the frame
        gaze (GazeTracking): Detect eyes in the frame
    """
    frame = frame.copy()
    if not face_detector.has_face and not gaze.pupils_located:
        timer.pause()
        cv2.putText(frame, "timer paused", (432, 40), FONT_3, 0.6, RED, 1)
    else:
        timer.start()
    time_duration: str = f"t. {(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(frame, time_duration, (500, 20), FONT_3, 0.8, BLUE, 1)

    return frame


def do_posture_watch(frame: ColorImage, mymodel, mode: PostureMode) -> ColorImage:
    """Returns the frame with posture label text.

    Arguments:
        frame (NDArray[(Any, Any, 3), UInt8]): The image contains posture to be watched
        mymodel (tensorflow.keras.Model): To predict the label of frame
        mode (PostureMode): The mode will also be part of the text
    """
    im_color: ColorImage = frame.copy()
    im: GrayImage = cv2.cvtColor(im_color, cv2.COLOR_BGR2GRAY)

    im = cv2.resize(im, image_dimensions)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *image_dimensions, 1)

    # 2 cuz there are 2 PostureLabels
    predictions: NDArray[(1, 2), Float[32]] = mymodel.predict(im)
    class_pred: Int[64] = np.argmax(predictions)
    conf: Float[32] = predictions[0][class_pred]

    im_color = cv2.resize(im_color, (640, 480), interpolation=cv2.INTER_AREA)

    if class_pred == PostureLabel.slump.value:
        im_color = cv2.putText(im_color, f'{mode.name}-slump', (10, 70), FONT_0, 1, RED, thickness=2)
    else:
        im_color = cv2.putText(im_color, f'{mode.name}-good', (10, 70), FONT_0, 1, GREEN, thickness=2)

    msg: str = f'confidence {round(int(conf*100))}%'
    im_color = cv2.putText(im_color, msg, (15, 110), FONT_0, 0.6, (200, 200, 255), thickness=2)
    return im_color
