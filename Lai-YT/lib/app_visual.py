"""
Visualized version of applications. No warning, detection only.
Specific design for alpha.py.
"""

import cv2
import dlib
import numpy
from imutils import face_utils
from nptyping import Float, Int, NDArray

from .color import BLUE, GREEN, MAGENTA, RED
from .cv_font import FONT_0
from .image_type import ColorImage, GrayImage
from .train import PostureLabel, IMAGE_DIMENSIONS


def put_distance_text(canvas: ColorImage, distance: float) -> ColorImage:
    """Returns the canvas with distance text.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): Imgae to put text on
        distance (float)
    """
    canvas = canvas.copy()
    text = "dist. " + str(round(distance, 2))
    cv2.putText(canvas, text, (10, 30), FONT_0, 0.9, MAGENTA, 2)
    return canvas


def record_focus_time(canvas: ColorImage, time: float, paused: bool) -> ColorImage:
    """Returns the canvas with time record, also extra text if paused.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to put time record on, it'll be copied
        time (float)
        paused (bool)
    """
    canvas = canvas.copy()
    time_duration: str = f"t. {(time // 60):02d}:{(time % 60):02d}"
    cv2.putText(canvas, time_duration, (500, 20), FONT_0, 0.8, BLUE, 1)

    if paused:
        cv2.putText(canvas, "time pause", (500, 40), FONT_0, 0.6, RED, 1)
    return canvas


def mark_face(canvas: ColorImage, face: dlib.rectangle, shape: dlib.full_object_detection) -> ColorImage:
    """Returns the canvas with face area framed up and landmarks dotted.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to mark face on, it'll be copied
        face (dlib.rectangle): Face data detected by dlib.fhog_object_detector
        shape (dlib.full_object_detection): Landmarks detected by dlib.shape_predictor
    """
    # face area
    fx, fy, fw, fh = face_utils.rect_to_bb(face)
    cv2.rectangle(canvas, (fx, fy), (fx+fw, fy+fh), MAGENTA, 1)
    # face landmarks
    shape_: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(shape)
    for lx, ly in shape_:
        cv2.circle(canvas, (lx, ly), 1, GREEN, -1)
    return canvas


def do_posture_angle_check(canvas: ColorImage, angle: float, threshold: float) -> ColorImage:
    """Returns the canvas with posture and angle text on it.
    "Good" in green if angle doesn't exceed the threshold, otherwise "Slump" in red.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to put text on, it'll be copied
        angle (float): The angle between the middle line of face and the vertical line of image
        threshold (float): Larger than this is considered to be a slump posture
    """
    text, color = ("Good", GREEN) if abs(angle) < threshold else ("Slump", RED)

    # try to match the style in do_posture_model_predict()
    cv2.putText(canvas, text, (10, 70), FONT_0, 0.9, color, 2)
    cv2.putText(canvas, f"Slope Angle: {round(angle, 1)} degrees", (15, 110), FONT_0, 0.7, (200, 200, 255), 2)
    return canvas


def do_posture_model_predict(frame: ColorImage, mymodel, canvas: ColorImage) -> ColorImage:
    """Returns the canvas with posture label text.

    Arguments:
        frame (NDArray[(Any, Any, 3), UInt8]): The image contains posture to be watched, it'll be copied
        mymodel (tensorflow.keras.Model): To predict the label of frame
        canvas (NDArray[(Any, Any, 3), UInt8]): The prediction will be texted on the canvas
    """
    im: GrayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    im = cv2.resize(im, IMAGE_DIMENSIONS)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *IMAGE_DIMENSIONS, 1)

    # 2 cuz there are 2 PostureLabels
    predictions: NDArray[(1, 2), Float[32]] = mymodel.predict(im)
    class_pred: Int[64] = numpy.argmax(predictions)
    conf: Float[32] = predictions[0][class_pred]

    canvas = cv2.resize(canvas, (640, 480), interpolation=cv2.INTER_AREA)

    if class_pred == PostureLabel.slump.value:
        cv2.putText(canvas, "Slump", (10, 70), FONT_0, 0.9, RED, thickness=2)
    else:
        cv2.putText(canvas, "Good", (10, 70), FONT_0, 0.9, GREEN, thickness=2)

    msg: str = f'Predict Conf.: {round(int(conf*100))}%'
    cv2.putText(canvas, msg, (15, 110), FONT_0, 0.7, (200, 200, 255), thickness=2)
    return canvas
