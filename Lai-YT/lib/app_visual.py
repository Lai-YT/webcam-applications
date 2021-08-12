"""
Visualized version of applications. No warning, detection only.
Specific design for alpha.py.
"""

import cv2
import numpy as np
from playsound import playsound
from nptyping import Float, Int, NDArray
from typing import Any, Optional

from .color import BLUE, GREEN, MAGENTA, RED
from .cv_font import FONT_0, FONT_3
from .distance_detector import DistanceDetector
from .face_angle_detector import FaceAngleDetector
from .face_detector import FaceDetector
from .image_type import ColorImage, GrayImage
from .timer import Timer
from .train import PostureMode, PostureLabel, image_dimensions


def do_distance_measurement(canvas: ColorImage, distance_detector: DistanceDetector) -> ColorImage:
    """Returns the canvas with distance text, which is held by the DistanceDetector.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): Imgae to put text on
        distance_detector (DistanceDetector): The detector used to estimate the distance
    """
    canvas = canvas.copy()
    distance: Optional[float] = distance_detector.distance()
    text: str = ""
    if distance is not None:
        distance = distance_detector.distance()
        text = "dist. " + str(round(distance, 2))
    else:
        text = "Face width unclear."
    cv2.putText(canvas, text, (10, 30), FONT_3, 0.9, MAGENTA, 2)

    return canvas


def do_focus_time_record(canvas: ColorImage, timer: Timer, face_detector: FaceDetector, angle_detector: FaceAngleDetector) -> ColorImage:
    """If there are faces or eyes detected by the detectors, the timer wil keep timing, otherwise stops.
    Returns the canvas with time stamp.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to put time stamp on
        timer (Timer): The timer object that records the time
        face_detector (FaceDetector): Knows whether there are faces or not
        angle_detector (FaceAngleDetector): Knows whether there are faces or not
    """
    canvas = canvas.copy()
    if not face_detector.has_face and not angle_detector.angles():
        timer.pause()
        cv2.putText(canvas, "time pause", (500, 40), FONT_3, 0.6, RED, 1)
    else:
        timer.start()

    time_duration: str = f"t. {(timer.time() // 60):02d}:{(timer.time() % 60):02d}"
    cv2.putText(canvas, time_duration, (500, 20), FONT_3, 0.8, BLUE, 1)
    return canvas


def do_posture_angle_check(canvas: ColorImage, angle: float, threshold: float) -> ColorImage:
    """Returns the canvas with posture and angle text on it.
    "Good" in green if angle doesn't exceed the threshold, otherwise "Slump" in red.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to put text on
        angle (float): The angle between the middle line of face and the vertical line of image
        threshold (float): Larger than this is considered to be a slump posture
    """
    text, color = ("Good", GREEN) if abs(angle) < threshold else ("Slump", RED)

    # try to match the style in do_posture_model_predict()
    cv2.putText(canvas, text, (10, 70), FONT_3, 0.9, color, 2)
    cv2.putText(canvas, f"Slope Angle: {round(angle, 1)} degrees", (15, 110), FONT_3, 0.7, (200, 200, 255), 2)
    return canvas


def do_posture_model_predict(frame: ColorImage, mymodel, canvas: ColorImage) -> ColorImage:
    """Returns the canvas with posture label text.

    Arguments:
        frame (NDArray[(Any, Any, 3), UInt8]): The image contains posture to be watched
        mymodel (tensorflow.keras.Model): To predict the label of frame
        canvas (NDArray[(Any, Any, 3), UInt8]): The prediction will be texted on the canvas
    """
    im: GrayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    im = cv2.resize(im, image_dimensions)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *image_dimensions, 1)

    # 2 cuz there are 2 PostureLabels
    predictions: NDArray[(1, 2), Float[32]] = mymodel.predict(im)
    class_pred: Int[64] = np.argmax(predictions)
    conf: Float[32] = predictions[0][class_pred]

    canvas = cv2.resize(canvas, (640, 480), interpolation=cv2.INTER_AREA)

    if class_pred == PostureLabel.slump.value:
        cv2.putText(canvas, "Slump", (10, 70), FONT_0, 0.9, RED, thickness=2)
    else:
        cv2.putText(canvas, "Good", (10, 70), FONT_0, 0.9, GREEN, thickness=2)

    msg: str = f'Predict Conf.: {round(int(conf*100))}%'
    cv2.putText(canvas, msg, (15, 110), FONT_0, 0.7, (200, 200, 255), thickness=2)
    return canvas
