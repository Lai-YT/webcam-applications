"""
Visualized version of applications. No warning, detection only.
Specific design for alpha.py.
"""

from typing import List, Tuple

import cv2
import numpy
from nptyping import Float, Int, NDArray

from lib.color import BLUE, GREEN, MAGENTA, RED
from lib.cv_font import FONT_0, FONT_3
from lib.image_type import ColorImage, GrayImage
from lib.timer import Timer
from lib.train import PostureLabel, IMAGE_DIMENSIONS
from gui.warning_shower import TimeShower


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


class DistanceSentinel:
    def __init__(self, distance_calculator, warn_dist: float) -> None:
        """
        Arguments:
            distance_calculator (DistanceCalculator): Use to calculate the distance between face and screen
            warn_dist (float): Distance closer than this is to be warned
        """
        self._distance_calculator = distance_calculator
        self._warn_dist = warn_dist

    def warn_if_too_close(self, canvas: ColorImage, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Warning message shows when the distance is less than warn_dist.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8])
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        distance = self._distance_calculator.calculate(landmarks)

        # warning logic...
        self.put_distance_text(canvas, distance)
        if distance < self._warn_dist:
            cv2.putText(canvas, 'too close', (10, 150), FONT_0, 0.9, RED, 2)

    def put_distance_text(self, canvas: ColorImage, distance: float) -> None:
        """Puts distance text on the canvas.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): Imgae to put text on
            distance (float): The distance to be put
        """
        text = "dist. " + str(round(distance, 2))
        cv2.putText(canvas, text, (10, 30), FONT_0, 0.9, MAGENTA, 2)


class TimeSentinel:
    """
    TimeSentinel checks if the time held by a Timer exceeds time limit and
    interacts with a TimeShower to show the corresponding TimerWidget.
    """
    def __init__(self, time_limit: int, break_time: int):
        """
        Arguments:
            time_limit (int): Triggers a break if reached (minutes)
            break_time (int): How long the break should be (minutes)
        """
        # minute to second
        self._time_limit = time_limit * 60
        self._break_time = break_time * 60
        self._break_timer = Timer()
        self._time_shower = TimeShower()

    def break_time_if_too_long(self, canvas: ColorImage, timer: Timer) -> None:
        """If the time record in the Timer object exceeds time limit, a break time countdown shows on the center of the canvas.
        The timer will be paused during the break, reset after the break.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): The image to show break time information
            timer (Timer): Contains time record
        """
        # Break time is over, reset the timer for a new start.
        if self._break_timer.time() > self._break_time:
            timer.reset()
            self._break_timer.reset()
            self._time_shower.switch_time_state("work")
        # not the time to take a break
        elif timer.time() < self._time_limit:
            # The time of the normal timer is to be shown.
            self._time_shower.update_time(timer.time())

            # Time record is only shown when not during the break.
            self.record_focus_time(canvas, timer.time(), timer.is_paused())
        else:
            if self._break_timer.time() == 0:
                self._time_shower.switch_time_state("break")

            timer.pause()
            self._break_timer.start()
            countdown: int = self._break_time - self._break_timer.time()
            # The time (countdown) of the break timer is to be shown.
            self._time_shower.update_time(countdown)

            time_left: str = f"{(countdown // 60):02d}:{(countdown % 60):02d}"
            cv2.putText(canvas, "break left: " + time_left, (450, 80), FONT_3, 0.6, GREEN, 1)

    def record_focus_time(self, canvas: ColorImage, time: float, paused: bool) -> None:
        """Puts time record on the canvas, also extra text if paused.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): The image to put time record on
            time (float)
            paused (bool)
        """
        time_duration: str = f"t. {(time // 60):02d}:{(time % 60):02d}"
        cv2.putText(canvas, time_duration, (500, 20), FONT_0, 0.8, BLUE, 1)

        if paused:
            cv2.putText(canvas, "time paused", (500, 40), FONT_0, 0.6, RED, 1)


class PostureChecker:
    def __init__(self, model, angle_calculator, warn_angle: float):
        """
        Arguments:
            model (tensorflow.keras.Model): Used to predict the label of image when a clear face isn't found
            angle_calculator (AngleCalculator): Used to calculate the angle of face when a face is found
            warn_angle (float): Face slope angle larger than this is considered to be a slump posture
        """
        self._model = model
        self._angle_calculator = angle_calculator
        self._warn_angle = warn_angle

    def check_posture(self, canvas: ColorImage, frame: ColorImage, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """If the landmarks of face are clear, use AngleCalculator to calculate the slope
        precisely; otherwise use the model to predict the posture.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): The prediction will be texted on the canvas
            frame (NDArray[(Any, Any, 3), UInt8]): The image contains posture to be watched
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        if landmarks.any():
            self.do_posture_angle_check(canvas, self._angle_calculator.calculate(landmarks))
        else:
            self.do_posture_model_predict(canvas, frame)

    def do_posture_angle_check(self, canvas: ColorImage, angle: float) -> None:
        """Puts posture and angle text on the canvas.
        "Good" in green if angle doesn't exceed the warn_angle, otherwise "Slump" in red.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): The image to put text on
            angle (float): The angle between the middle line of face and the vertical line of image
        """
        text, color = ("Good", GREEN) if abs(angle) < self._warn_angle else ("Slump", RED)

        # try to match the style in do_posture_model_predict()
        cv2.putText(canvas, text, (10, 70), FONT_0, 0.9, color, 2)
        cv2.putText(canvas, f"Slope Angle: {round(angle, 1)} degrees", (15, 110), FONT_0, 0.7, (200, 200, 255), 2)

    def do_posture_model_predict(self, canvas: ColorImage, frame: ColorImage) -> None:
        """Puts posture label text on the canvas.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): The prediction will be texted on the canvas
            frame (NDArray[(Any, Any, 3), UInt8]): The image contains posture to be watched
        """
        im: GrayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        im = cv2.resize(im, IMAGE_DIMENSIONS)
        im = im / 255  # Normalize the image
        im = im.reshape(1, *IMAGE_DIMENSIONS, 1)

        # 2 cuz there are 2 PostureLabels
        predictions: NDArray[(1, 2), Float[32]] = self._model.predict(im)
        class_pred: Int[64] = numpy.argmax(predictions)
        conf: Float[32] = predictions[0][class_pred]

        cv2.resize(canvas, (640, 480), interpolation=cv2.INTER_AREA)

        if class_pred == PostureLabel.slump.value:
            cv2.putText(canvas, "Slump", (10, 70), FONT_0, 0.9, RED, thickness=2)
        else:
            cv2.putText(canvas, "Good", (10, 70), FONT_0, 0.9, GREEN, thickness=2)

        msg: str = f'Predict Conf.: {conf:.0%}'
        cv2.putText(canvas, msg, (15, 110), FONT_0, 0.7, (200, 200, 255), thickness=2)
