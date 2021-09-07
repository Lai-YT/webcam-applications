"""
Visualized version of applications. No warning, detection only.
Specific design for alpha.py.
"""

from typing import List, Tuple

import cv2
import numpy
from nptyping import Float, Int, NDArray
from tensorflow.keras import models

from lib.color import BLUE, GREEN, MAGENTA, RED
from lib.cv_font import FONT_0, FONT_3
from lib.image_type import ColorImage, GrayImage
from lib.timer import Timer
from lib.train import PostureLabel, IMAGE_DIMENSIONS
from gui.timer_window import TimerGui


def put_distance_text(canvas: ColorImage, distance: float) -> None:
    """Puts distance text on the canvas.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): Imgae to put text on
        distance (float)
    """
    text = "dist. " + str(round(distance, 2))
    cv2.putText(canvas, text, (10, 30), FONT_0, 0.9, MAGENTA, 2)


def record_focus_time(canvas: ColorImage, time: float, paused: bool) -> None:
    """Puts time record on the canvas, also extra text if paused.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to put time record on
        time (float)
        paused (bool)
    """
    time_duration: str = f"t. {(time // 60):02d}:{(time % 60):02d}"
    cv2.putText(canvas, time_duration, (520, 20), FONT_0, 0.8, BLUE, 1)

    if paused:
        cv2.putText(canvas, "time paused", (500, 40), FONT_0, 0.6, RED, 1)


def mark_face(canvas: ColorImage, face: Tuple[int, int, int, int], landmarks: NDArray[(68, 2), Int[32]]) -> None:
    """Modifies the canvas with face area framed up and landmarks dotted.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to mark face on
        face (int, int, int, int): Upper-left x, y coordinates of face and it's width, height
        landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
    """
    fx, fy, fw, fh = face
    cv2.rectangle(canvas, (fx, fy), (fx+fw, fy+fh), MAGENTA, 1)
    for lx, ly in landmarks:
        cv2.circle(canvas, (lx, ly), 1, GREEN, -1)


break_timer = Timer()
def break_time_if_too_long(canvas: ColorImage, timer: Timer, time_limit: int, break_time: int) -> None:
    """If the time record in the Timer object exceeds time limit, a break time countdown shows on the center of the canvas.
    The timer will be paused during the break, reset after the break.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to show break time information
        timer (Timer): Contains time record
        time_limit (int): Triggers a break if reached (minutes)
        break_time (int): How long the break should be (minutes)
    """
    # minute to second
    time_limit *= 60
    break_time *= 60
    # Break time is over, reset the timer for a new start.
    if break_timer.time() > break_time:
        timer.reset()
        break_timer.reset()
        return
    # not the time to take a break
    if timer.time() < time_limit:
        #timer_gui.break_message_clear()
        return

    timer.pause()
    break_timer.start()
    countdown: int = break_time - break_timer.time()
    time_left: str = f"{(countdown // 60):02d}:{(countdown % 60):02d}"

    cv2.putText(canvas, "break left: " + time_left, (450, 65), FONT_3, 0.6, GREEN, 1)



def do_posture_angle_check(canvas: ColorImage, angle: float, threshold: float) -> None:
    """Puts posture and angle text on the canvas.
    "Good" in green if angle doesn't exceed the threshold, otherwise "Slump" in red.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to put text on
        angle (float): The angle between the middle line of face and the vertical line of image
        threshold (float): Larger than this is considered to be a slump posture
    """
    text, color = ("Good", GREEN) if abs(angle) < threshold else ("Slump", RED)

    # try to match the style in do_posture_model_predict()
    cv2.putText(canvas, text, (10, 70), FONT_0, 0.9, color, 2)
    cv2.putText(canvas, f"Slope Angle: {round(angle, 1)} degrees", (15, 110), FONT_0, 0.7, (200, 200, 255), 2)


def do_posture_model_predict(frame: ColorImage, model: models, canvas: ColorImage) -> None:
    """Puts posture label text on the canvas.

    Arguments:
        frame (NDArray[(Any, Any, 3), UInt8]): The image contains posture to be watched
        model (tensorflow.keras.Model): To predict the label of frame
        canvas (NDArray[(Any, Any, 3), UInt8]): The prediction will be texted on the canvas
    """
    im: GrayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    im = cv2.resize(im, IMAGE_DIMENSIONS)
    im = im / 255  # Normalize the image
    im = im.reshape(1, *IMAGE_DIMENSIONS, 1)

    # 2 cuz there are 2 PostureLabels
    predictions: NDArray[(1, 2), Float[32]] = model.predict(im)
    class_pred: Int[64] = numpy.argmax(predictions)
    conf: Float[32] = predictions[0][class_pred]

    cv2.resize(canvas, (640, 480), interpolation=cv2.INTER_AREA)

    if class_pred == PostureLabel.slump.value:
        cv2.putText(canvas, "Slump", (10, 70), FONT_0, 0.9, RED, thickness=2)
    else:
        cv2.putText(canvas, "Good", (10, 70), FONT_0, 0.9, GREEN, thickness=2)

    msg: str = f'Predict Conf.: {round(int(conf*100))}%'
    cv2.putText(canvas, msg, (15, 110), FONT_0, 0.7, (200, 200, 255), thickness=2)


def warn_if_too_close(canvas: ColorImage, distance: float, warn_dist: float) -> None:
    """Warning message shows when the distance is less than warn_dist.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8])
        distance (float)
        warn_dist (float)
    """
    if distance < warn_dist:
        cv2.putText(canvas, 'too close', (10, 150), FONT_0, 0.9, RED, 2)
