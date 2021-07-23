"""
Visualized version of applications. No warning, detection only.
Specific design for demo.py.
"""

import cv2
import numpy as np
from playsound import playsound
from tensorflow.keras import models

from .color import *
from .cv_font import *
from .face_distance_detector import FaceDistanceDetector
from .gaze_tracking import GazeTracking
from .path import to_abs_path
from .timer import Timer

# for posture watch
model_path: str = to_abs_path("trained_models/posture_model.h5")
mp3file: str = to_abs_path("sounds/what.mp3")
image_dimensions: Tuple[int, int] = (224, 224)

# type hints
Image = np.ndarray

def do_distance_measurement(frame: Image, distance_detector: FaceDistanceDetector, *, face_only: bool = False) -> Image:
    """Estimates the distance in the frame by FaceDistanceDetector.
    Returns the frame with distance text.

    Arguments:
        frame (numpy.ndarray): Imgae with face to be detected
        distance_detector (FaceDistanceDetector): The detector used to detect the face and estimate the distance

    Keyword Arguments:
        face_only (bool): No distance text on frame if True
    """
    frame = frame.copy()
    distance_detector.estimate(frame)
    frame = distance_detector.annotated_frame()
    if not face_only:
        text: str = ""
        if distance_detector.has_face:
            distance = distance_detector.distance()
            text = "dist. " + str(int(distance))
        else:
            text = "No face detected."
        cv2.putText(frame, text, (60, 30), FONT_3, 0.9, MAGENTA, 1)

    return frame


def do_gaze_tracking(frame: Image, gaze: GazeTracking) -> Image:
    """Locate the position of eyes in frame.
    Returns the frame with eye marked.

    Arguments:
        frame (numpy.ndarray): Imgae with eyes to be located
        gaze (GazeTracking): Used to locate the position
    """
    frame = frame.copy()
    # We send this frame to GazeTracking to analyze it
    gaze.refresh(frame)
    frame = gaze.annotated_frame()
    return frame


def do_focus_time_record(frame: Image, timer: Timer, face_detector: FaceDistanceDetector, gaze: GazeTracking) -> Image:
    """If there's face or eyes in the frame, the timer wil keep timing, otherwise stops.
    Returns the frame with time stamp.

    Arguments:
        frame (numpy.ndarray): The image to detect whether the user is gazing
        timer (Timer): The timer object that records the time
        face_detector (FaceDistanceDetector): Detect face in the frame
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


def load_posture_model():
    """Returns the model trained by do_training()"""
    return models.load_model(model_path)


def do_posture_watch(frame: Image, mymodel) -> Image:
    """Returns the frame with posture label text, also mp3 will be played when posture slumpled.

    Arguments:
        frame (numpy.ndarray): The image contains posture to be watched
        mymodel (tensorflow.keras.Model): To predict the label of frame
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

    if class_pred == 1:
        # Slumped
        im_color = cv2.putText(im_color, 'Slumped', (10, 70), FONT_0, 1, RED, thickness=3)
        playsound(mp3file)
    else:
        im_color = cv2.putText(im_color, 'Good', (10, 70), FONT_0, 1, GREEN, thickness=2)

    msg: str = f'Confidence {round(int(conf*100))}%'
    im_color = cv2.putText(im_color, msg, (15, 110), FONT_0, 0.6, (200, 200, 255), thickness=2)
    return im_color
