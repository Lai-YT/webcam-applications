from typing import List, Optional, Tuple

import cv2
import numpy
from nptyping import Float, Int, NDArray
from playsound import playsound

from lib.color import BLUE, GREEN, MAGENTA, RED
from lib.concentration_grader import ConcentrationGrader
from lib.cv_font import FONT_0, FONT_3
from lib.image_type import ColorImage, GrayImage
from lib.path import to_abs_path
from lib.timer import Timer
from lib.train import ModelTrainer, PostureLabel
from gui.popup_shower import TimeShower


# Module scope grader for all guards to share.
_concentration_grader = ConcentrationGrader(interval=100)


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
    def __init__(self, distance_calculator=None, warn_dist: Optional[float] = None) -> None:
        """
        Arguments:
            distance_calculator (DistanceCalculator): Use to calculate the distance between face and screen
            warn_dist (float): Distance closer than this is to be warned
        """
        if distance_calculator is not None:
            self._distance_calculator = distance_calculator
        if warn_dist is not None:
            self._warn_dist = warn_dist

        self._warning_enabled = True
        self._wavfile = to_abs_path("sounds/too_close.wav")
        self._warning_repeat_timer = Timer()
        # To avoid double play due to a near time check (less than 1 sec).
        self._f_played = False

    def set_distance_calculator(self, distance_calculator) -> None:
        self._distance_calculator = distance_calculator

    def set_warn_dist(self, warn_dist: float) -> None:
        self._warn_dist = warn_dist

    def set_warning_enabled(self, enabled: bool) -> None:
        self._warning_enabled = enabled

    def warn_if_too_close(self, canvas: ColorImage, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Warning message shows when the distance is less than warn_dist.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8])
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        if not hasattr(self, "_distance_calculator") or not hasattr(self, "_warn_dist"):
            # Should do nothing if the sentinel is not ready.
            return

        distance = self._distance_calculator.calculate(landmarks)

        # warning logic...
        self._put_distance_text(canvas, distance)
        if distance < self._warn_dist:
            # Too close is considered to be a distraction.
            _concentration_grader.increase_distraction()

            cv2.putText(canvas, "too close", (10, 150), FONT_0, 0.9, RED, 2)
            # If this is a new start of a too-close interval,
            # play sound and start another interval.
            if not self._f_played:
                self._f_played = True
                self._warning_repeat_timer.start()
                if self._warning_enabled:
                    playsound(self._wavfile, block=False)
            # Every 9 seconds of a "consecutive" too-close, sound is repeated.
            # Note that the sound file is about 4 sec, take 5 sec as the interval.
            elif self._warning_repeat_timer.time() > 9:
                # Reset the timer and flag, so can be caught as a new start of interval.
                self._f_played = False
                self._warning_repeat_timer.reset()
        # Reset the timer once after an short interval.
        # This can avoid sounds from overlapping when moving between proper and non-proper distance.
        elif self._warning_repeat_timer.time() > 8:
            self._f_played = False
            self._warning_repeat_timer.reset()

        if distance < self._warn_dist:
            # Too close is considered to be a distraction.
            _concentration_grader.increase_distraction()
        else:
            _concentration_grader.increase_concentration()

    def _put_distance_text(self, canvas: ColorImage, distance: float) -> None:
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
    def __init__(self, time_limit: Optional[int] = None, break_time: Optional[int] = None):
        """
        Arguments:
            time_limit (int): Triggers a break if reached (minutes)
            break_time (int): How long the break should be (minutes)
        """
        if time_limit is not None:
            # minute to second
            self._time_limit = time_limit * 60
        if break_time is not None:
            self._break_time = break_time * 60

        self._f_break_started = False
        self._break_timer = Timer()
        self._warning_enabled = True
        self._time_shower = TimeShower()

    def set_time_limit(self, time_limit: int) -> None:
        self._time_limit = time_limit * 60

    def set_break_time(self, break_time: int) -> None:
        self._break_time = break_time * 60

    def set_warning_enabled(self, enabled: bool) -> None:
        self._warning_enabled = enabled

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
            # Set the flag and play the sound when leaving break.
            self._f_break_started = False
            if self._warning_enabled:
                playsound(to_abs_path("sounds/break_over.wav"), block=False)
        # not the time to take a break
        elif timer.time() < self._time_limit:
            # The time of the normal timer is to be shown.
            self._time_shower.update_time(timer.time())

            # Time record is only shown when not during the break.
            self.record_focus_time(canvas, timer.time(), timer.is_paused())

            # Timer is paused if there's no face, which is considered to be a distraction.
            # Not count during break time.
            if timer.is_paused():
                _concentration_grader.increase_distraction()
            else:
                _concentration_grader.increase_concentration()
        else:
            if not self._f_break_started:
                self._time_shower.switch_time_state("break")
                self._f_break_started = True
                if self._warning_enabled:
                    # Note that using flag instead of checking time to avoid double playing
                    # since the interval between time checkings is often less than 1 sec.
                    playsound(to_abs_path("sounds/break_start.wav"), block=False)

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

    def close_timer_widget(self):
        self._time_shower.close_timer_widget()
        # If not reset timer, a break-time-close might keep the countdown to next start.
        # (no effect if every start is a fresh new sentinel)
        self._break_timer.reset()


class PostureChecker:
    def __init__(self, model=None, angle_calculator=None, warn_angle: Optional[float] = None):
        """
        Arguments:
            model (tensorflow.keras.Model): Used to predict the label of image when a clear face isn't found
            angle_calculator (AngleCalculator): Used to calculate the angle of face when a face is found
            warn_angle (float): Face slope angle larger than this is considered to be a slump posture
        """
        if model is not None:
            self._model = model
        if angle_calculator is not None:
            self._angle_calculator = angle_calculator
        if warn_angle is not None:
            self._warn_angle = warn_angle

        self._warning_enabled = True
        self._wavfile = to_abs_path("sounds/posture_slump.wav")
        self._warning_repeat_timer = Timer()
        # To avoid double play due to a near time check (less than 1 sec).
        self._f_played = False

    def set_model(self, model) -> None:
        self._model = model

    def set_angle_calculator(self, angle_calculator) -> None:
        self._angle_calculator = angle_calculator

    def set_warn_angle(self, warn_angle: float) -> None:
        self._warn_angle = warn_angle

    def set_warning_enabled(self, enabled: bool) -> None:
        self._warning_enabled = enabled

    def check_posture(self, canvas: ColorImage, frame: ColorImage, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Sound plays if is a "slump" posture.
        If the landmarks of face are clear, use AngleCalculator to calculate the slope
        precisely; otherwise use the model to predict the posture.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): The prediction will be texted on the canvas
            frame (NDArray[(Any, Any, 3), UInt8]): The image contains posture to be watched
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        if landmarks.any():
            good: bool = self._do_posture_angle_check(canvas, self._angle_calculator.calculate(landmarks))
        else:
            good = self._do_posture_model_predict(canvas, frame)

        if not good:
            # If this is a new start of a slumped posture interval,
            # play sound and start another interval.
            if not self._f_played:
                self._f_played = True
                self._warning_repeat_timer.start()
                if self._warning_enabled:
                    playsound(self._wavfile, block=False)
            # Every 9 seconds of a "consecutive" slump, sound is repeated.
            # Note that the sound file is about 4 sec, take 5 sec as the interval.
            elif self._warning_repeat_timer.time() > 9:
                # Reset the timer and flag, so can be caught as a new start of interval.
                self._f_played = False
                self._warning_repeat_timer.reset()
        # Reset the timer once after an interval.
        # This can avoid sounds from overlapping when sitching between "Good" and "Slump"
        elif self._warning_repeat_timer.time() > 8:
            self._f_played = False
            self._warning_repeat_timer.reset()

        if not good:
            _concentration_grader.increase_distraction()
        else:
            _concentration_grader.increase_concentration()

        text, color = ("Good", GREEN) if good else ("Slump", RED)
        cv2.putText(canvas, text, (10, 70), FONT_0, 0.9, color, thickness=2)

    def _do_posture_angle_check(self, canvas: ColorImage, angle: float) -> bool:
        """Returns True if is a "Good" posture.
        Also puts posture and angle text on the canvas. "Good" in green if angle
        doesn't exceed the warn_angle, otherwise "Slump" in red.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): The image to put text on
            angle (float): The angle between the middle line of face and the vertical line of image
        """
        good: bool = abs(angle) < self._warn_angle

        cv2.putText(canvas, f"Slope Angle: {round(angle, 1)} degrees", (15, 110), FONT_0, 0.7, (200, 200, 255), 2)

        return good

    def _do_posture_model_predict(self, canvas: ColorImage, frame: ColorImage) -> bool:
        """Returns True if is a "Good" posture.
        Also puts posture label text on the canvas.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]): The prediction will be texted on the canvas
            frame (NDArray[(Any, Any, 3), UInt8]): The image contains posture to be watched
        """
        im: GrayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        im = cv2.resize(im, ModelTrainer.IMAGE_DIMENSIONS)
        im = im / 255  # Normalize the image
        im = im.reshape(1, *ModelTrainer.IMAGE_DIMENSIONS, 1)

        # 2 cuz there are 2 PostureLabels
        predictions: NDArray[(1, 2), Float[32]] = self._model.predict(im)
        class_pred: Int[64] = numpy.argmax(predictions)
        conf: Float[32] = predictions[0][class_pred]
        good: bool = (class_pred == PostureLabel.good.value)

        cv2.resize(canvas, (640, 480), interpolation=cv2.INTER_AREA)

        msg: str = f'Predict Conf.: {conf:.0%}'
        cv2.putText(canvas, msg, (15, 110), FONT_0, 0.7, (200, 200, 255), thickness=2)

        return good
