from enum import Enum, auto
from typing import List, Optional, Tuple

import cv2
import numpy
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from nptyping import Float, Int, NDArray
from playsound import playsound
from tensorflow.python.keras.engine.sequential import Sequential

from lib.angle_calculator import AngleCalculator
from lib.color import GREEN, MAGENTA, RED
from lib.concentration_grader import ConcentrationGrader
from lib.cv_font import FONT_0
from lib.distance_calculator import DistanceCalculator
from lib.image_type import ColorImage, GrayImage
from lib.path import to_abs_path
from lib.timer import Timer
from lib.train import ModelTrainer, PostureLabel
from gui.popup_shower import TimeShower
from gui.popup_widget import TimeState


# Module scope grader for all guards to share.
global_grader_for_guards = ConcentrationGrader(interval=100)


def mark_face(canvas: ColorImage, face: Tuple[int, int, int, int], landmarks: NDArray[(68, 2), Int[32]]) -> None:
    """Modifies the canvas with face area framed up and landmarks dotted.

    Arguments:
        canvas: The image to mark face on.
        face: Upper-left x, y coordinates of face and it's width, height.
        landmarks: (x, y) coordinates of the 68 face landmarks.
    """
    fx, fy, fw, fh = face
    cv2.rectangle(canvas, (fx, fy), (fx+fw, fy+fh), MAGENTA, 1)
    for lx, ly in landmarks:
        cv2.circle(canvas, (lx, ly), 1, GREEN, -1)


class DistanceState(Enum):
    """
    Two states represent two different relationships
    between distance and limit.
    """
    NORMAL = auto()
    WARNING = auto()


class DistanceGuard(QObject):
    """DistanceGuard checks whether the face obtained by the landmarks are at
    a short distance.

    Signals:
        s_distance_refreshed: Emits everytime a new distance is calculated.
    """

    s_distance_refreshed = pyqtSignal(float, DistanceState)

    def __init__(self,
                 distance_calculator: Optional[DistanceCalculator] = None,
                 warn_dist: Optional[float] = None,
                 warning_enabled: bool = True) -> None:
        """
        All arguments can be set later with their corresponding setters.

        Arguments:
            distance_calculator: Use to calculate the distance between face and screen.
            warn_dist : Distance closer than this is to be warned.
            warning_enabled:
                Whether there's sound that warns the user when the distance is
                too close.
        """
        super().__init__()

        if distance_calculator is not None:
            self._distance_calculator: DistanceCalculator = distance_calculator
        if warn_dist is not None:
            self._warn_dist: float = warn_dist
        # Sound warning is enabled as default.
        self._warning_enabled: bool = warning_enabled

        self._wavfile: str = to_abs_path("sounds/too_close.wav")
        self._warning_repeat_timer = Timer()
        # To avoid double play due to a near time check (less than 1 sec).
        self._f_played: bool = False

    def set_distance_calculator(self, distance_calculator: DistanceCalculator) -> None:
        """
        Arguments:
            distance_calculator: Use to calculate the distance between face and screen.
        """
        self._distance_calculator = distance_calculator

    def set_warn_dist(self, warn_dist: float) -> None:
        """
        Arguments:
            warn_dist : Distance closer than this is to be warned.
        """
        self._warn_dist = warn_dist

    def set_warning_enabled(self, enabled: bool) -> None:
        """
        Arguments:
            enabled: Whether there's sound that warns the user when the distance is too close.
        """
        self._warning_enabled = enabled

    def warn_if_too_close(self, canvas: ColorImage, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Warning message shows when the distance is less than warn_dist.

        Notice that this method does nothing if distance calculator haven't been
        set yet; no warning if warn dist haven't been set yet.

        Arguments:
            canvas: The image to put text on.
            landmarks: (x, y) coordinates of the 68 face landmarks.

        Emits:
            s_distance_refreshed: With the distance calculated.
        """
        # Can't do any thing without DistanceCalculator.
        if not hasattr(self, "_distance_calculator"):
            return
        # Distance can be calculated when DistanceCalculator exists.
        if hasattr(self, "_distance_calculator"):
            distance: float = self._distance_calculator.calculate(landmarks)
            self._put_distance_text(canvas, distance)
        # Has DistanceCalculator but no warn dist.
        # Send the distance with normal state. And no further process.
        if not hasattr(self, "_warn_dist"):
            self.s_distance_refreshed.emit(distance, DistanceState.NORMAL)
            return

        # warning logic...
        if distance < self._warn_dist and self._warning_enabled:
            # If this is a new start of a too-close interval,
            # play sound and start another interval.
            if not self._f_played:
                self._f_played = True
                self._warning_repeat_timer.start()
                playsound(self._wavfile, block=False)
            # Only after certain interval can the sound be repeated.
            # Note that the sound file is about 3 sec, take 5 sec as the delay.
            elif self._warning_repeat_timer.time() > 8:
                # Reset the timer and flag, so can be caught as a new start of interval.
                self._f_played = False
                self._warning_repeat_timer.reset()

        # default state
        state = DistanceState.NORMAL
        if distance < self._warn_dist:
            state = DistanceState.WARNING
            cv2.putText(canvas, "too close", (10, 150), FONT_0, 0.9, RED, 2)

        self.s_distance_refreshed.emit(distance, state)

        # The grading part.
        if distance < self._warn_dist:
            # Too close is considered to be a distraction.
            global_grader_for_guards.increase_distraction()
        else:
            global_grader_for_guards.increase_concentration()


    def _put_distance_text(self, canvas: ColorImage, distance: float) -> None:
        """Puts distance text on the canvas.

        Distance is rounded to two decimal places.

        Arguments:
            canvas: Imgae to put text on.
            distance: The distance to be put.
        """
        text = "dist. " + str(round(distance, 2))
        cv2.putText(canvas, text, (10, 30), FONT_0, 0.9, MAGENTA, 2)


class TimeGuard(QObject):
    """TimeGuard checks whether the time held by a Timer exceeds time limit
    and interacts with a TimeShower to show the corresponding TimerWidget.

    Signals:
        s_time_refreshed:
            Emits everytime break_time_if_too_long is called.
            If isn't time to take a break, the time held br timer and state work
            is sent; otherwise the countdown of break and state break is sent.
    """

    s_time_refreshed = pyqtSignal(int, TimeState)

    def __init__(self,
                 time_limit: Optional[int] = None,
                 break_time: Optional[int] = None,
                 warning_enabled: bool = True) -> None:
        """
        All arguments can be set later with their corresponding setters.

        Arguments:
            time_limit: Triggers a break if reached (minutes).
            break_time: How long the break should be (minutes).
            warning_enabled:
                Whether there's sound that plays when it's time to take a break
                and end a break.
        """
        super().__init__()

        if time_limit is not None:
            self._time_limit: int = TimeGuard._min_to_sec(time_limit)
        if break_time is not None:
            self._break_time: int = TimeGuard._min_to_sec(break_time)
        self._warning_enabled: bool = warning_enabled

        self._f_break_started: bool = False
        self._end_break_sound: str = to_abs_path("sounds/break_over.wav")
        self._enter_break_sound: str = to_abs_path("sounds/break_start.wav")
        self._break_timer = Timer()
        self._time_shower = TimeShower()

    def set_time_limit(self, time_limit: int) -> None:
        """
        Arguments:
            time_limit: Triggers a break if reached (minutes).
        """
        self._time_limit = TimeGuard._min_to_sec(time_limit)

    def set_break_time(self, break_time: int) -> None:
        """
        Arguments:
            break_time: How long the break should be (minutes).
        """
        self._break_time = TimeGuard._min_to_sec(break_time)

    def set_warning_enabled(self, enabled: bool) -> None:
        """
        Arguments:
            enabled:
                Whether there's sound that plays when it's time to take a break
                and end a break.
        """
        self._warning_enabled = enabled

    def break_time_if_too_long(self, timer: Timer) -> None:
        """The timer widget switches to break mode if the time held by timer exceeds
        the time limit.

        Notice that the time is simply updated to the timer widget and kept in
        work mode if time limit or break time haven't been set yet.

        Arguments:
            timer: Contains time record.

        Emits:
            s_time_refreshed:
                If isn't time to take a break, the time held by timer and work state is
                sent; otherwise the countdown of break and break state is sent.
        """
        if not hasattr(self, "_break_time") or not hasattr(self, "_time_limit"):
            # Only display the time if the guard is not ready.
            self._time_shower.update_time(timer.time())
            self.s_time_refreshed.emit(timer.time(), TimeState.WORK)
            return

        # Break time is over.
        if self._break_timer.time() > self._break_time:
            timer.reset()
            self._end_break()
        # not the time to take a break
        # Note that an extra flag check is to prevent state change during break
        # due to a time limit setting.
        elif timer.time() < self._time_limit and not self._f_break_started:
            # The time of the normal timer is to be shown.
            self._time_shower.update_time(timer.time())
            self.s_time_refreshed.emit(timer.time(), TimeState.WORK)
            # Timer is paused if there's no face, which is considered to be a distraction.
            # Not count during break time.
            if timer.is_paused():
                global_grader_for_guards.increase_distraction()
            else:
                global_grader_for_guards.increase_concentration()
        else:
            self._take_break()

    def show(self) -> None:
        """Shows the TimerWidget."""
        self._time_shower.show()

    def hide(self) -> None:
        """Hides the TimerWidget."""
        self._time_shower.hide()

    def reset(self) -> None:
        """If the TimeGuard is now taking a break, this method ends the break
        and switches back to work state.
        """
        self._f_break_started = False
        self._time_shower.switch_time_state(TimeState.WORK)
        self._break_timer.reset()

    @pyqtSlot()
    def close_timer_widget(self) -> None:
        self._time_shower.close_timer_widget()
        # If not reset, a break-time-close might keep the countdown to next start.
        # (no effect if every start is a fresh new guard)
        self.reset()

    def _take_break(self) -> None:
        """Updates the time of the break timer to the timer widget.

        Emits:
            s_time_refreshed: Emits with the countdown of break and the break state.
        """
        # If is the very moment to enter the break.
        if not self._f_break_started:
            self._enter_break()
        countdown: int = self._break_time - self._break_timer.time()
        # The time (countdown) of the break timer is to be shown.
        self._time_shower.update_time(countdown)
        self.s_time_refreshed.emit(countdown, TimeState.BREAK)

    def _enter_break(self) -> None:
        """Sound warning is played if it's enabled.

        Call this method if is the very moment to enter the break.
        """
        self._time_shower.switch_time_state(TimeState.BREAK)
        self._f_break_started = True
        self._break_timer.start()
        if self._warning_enabled:
            # Note that using flag instead of checking time to avoid double playing
            # since the interval between time checkings is often less than 1 sec.
            playsound(self._enter_break_sound, block=False)

    def _end_break(self) -> None:
        """Sound warning is played if it's enabled.

        Call this method if is the very moment to end the break.
        """
        self.reset()
        if self._warning_enabled:
            playsound(self._end_break_sound, block=False)

    @staticmethod
    def _min_to_sec(time_in_min: int) -> int:
        """Simple minute to second conversion method without any check."""
        return time_in_min * 60


class PostureGuard(QObject):
    """PostureGuard checks whether the face obtained by landmarks implies a
    good or slump posture.

    Signals:
        s_posture_refreshed:
            Emits everytime a posture is checked (all attributes need to be set).
            It sents the PostureLabel and the detail string of the
            determination.
    """

    s_posture_refreshed = pyqtSignal(PostureLabel, str)

    def __init__(self,
                 model: Optional[Sequential] = None,
                 angle_calculator: Optional[AngleCalculator] = None,
                 warn_angle: Optional[float] = None,
                 warning_enabled: bool = True) -> None:
        """
        All arguments can be set later with their corresponding setters.

        Arguments:
            model:
                Used to predict the label of image when a clear face isn't found.
            angle_calculator:
                Used to calculate the angle of face when a face is found.
            warn_angle:
                Face slope angle larger than this is considered to be a slump posture.
            warning_enabled:
                Whether there's sound that warns the user when a slump posture occurs.
        """
        super().__init__()

        if model is not None:
            self._model: Sequential = model
        if angle_calculator is not None:
            self._angle_calculator: AngleCalculator = angle_calculator
        if warn_angle is not None:
            self._warn_angle: float = warn_angle
        self._warning_enabled: bool = warning_enabled

        self._wavfile: str = to_abs_path("sounds/posture_slump.wav")
        self._warning_repeat_timer = Timer()
        # To avoid double play due to a near time check (less than 1 sec).
        self._f_played: bool = False

    def set_model(self, model: Sequential) -> None:
        """
        Arguments:
            model: Used to predict the label of image when a clear face isn't found.
        """
        self._model = model

    def set_angle_calculator(self, angle_calculator: AngleCalculator) -> None:
        """
        Arguments:
            angle_calculator: Used to calculate the angle of face when a face is found.
        """
        self._angle_calculator = angle_calculator

    def set_warn_angle(self, warn_angle: float) -> None:
        """
        Arguments:
            warn_angle: Face slope angle larger than this is considered to be a slump posture.
        """
        self._warn_angle = warn_angle

    def set_warning_enabled(self, enabled: bool) -> None:
        """
        Arguments:
            enabled: Whether there's sound that warns the user when a slump posture occurs.
        """
        self._warning_enabled = enabled

    def check_posture(self, canvas: ColorImage, frame: ColorImage, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Sound plays if is a "slump" posture and warning is enabled.

        If the landmarks of face are clear, use AngleCalculator to calculate the
        slope precisely; otherwise use the model to predict the posture.

        Notice that this method does nothing if angle calculator or warn angle
        haven't been set yet.

        Arguments:
            canvas: The prediction will be texted on the canvas.
            frame: The image contains posture to be watched.
            landmarks: (x, y) coordinates of the 68 face landmarks.

        Emits:
            s_posture_refreshed: Sends the posture label and result detail.

        Returns:
            The PostureLabel and the detail string of the determination.
            None if any of the necessary attributes aren't set.
        """
        if not hasattr(self, "_angle_calculator") or not hasattr(self, "_warn_angle"):
            return

        # Get posture label...
        if landmarks.any():
            posture, detail = self._do_posture_angle_check(canvas, self._angle_calculator.calculate(landmarks))
        else:
            posture, detail = self._do_posture_model_predict(canvas, frame)
        self.s_posture_refreshed.emit(posture, detail)

        # sound warning logic
        if posture is not PostureLabel.GOOD and self._warning_enabled:
            # If this is a new start of a slumped posture interval,
            # play sound then start another interval.
            if not self._f_played:
                self._f_played = True
                self._warning_repeat_timer.start()
                playsound(self._wavfile, block=False)
            # Only after certain interval can the sound be repeated.
            # Note that the sound file is about 3 sec, take 5 sec as the delay.
            elif self._warning_repeat_timer.time() > 8:
                # Reset the timer and flag, so can be caught as a new start of interval.
                self._f_played = False
                self._warning_repeat_timer.reset()

        # grade concentration
        if posture is not PostureLabel.GOOD:
            global_grader_for_guards.increase_distraction()
        else:
            global_grader_for_guards.increase_concentration()

        text, color = ("Good", GREEN) if posture is PostureLabel.GOOD else ("Slump", RED)
        cv2.putText(canvas, text, (10, 70), FONT_0, 0.9, color, thickness=2)

    def _do_posture_angle_check(self, canvas: ColorImage, angle: float) -> Tuple[PostureLabel, str]:
        """Puts posture and angle text on the canvas. "Good" in green if angle
        doesn't exceed the warn_angle, otherwise "Slump" in red.

        Arguments:
            canvas: The image to put text on.
            angle: The angle between the middle line of face and the vertical line of image.

        Returns:
            The PostureLabel and the detail string of the determination.
        """
        detail: str = f"by angle: {round(angle, 1)} degrees"
        cv2.putText(canvas, detail, (15, 110), FONT_0, 0.7, (200, 200, 255), 2)

        return (PostureLabel.GOOD if abs(angle) < self._warn_angle else PostureLabel.SLUMP), detail

    def _do_posture_model_predict(self, canvas: ColorImage, frame: ColorImage) -> Tuple[PostureLabel, str]:
        """Puts posture label text on the canvas.

        Arguments:
            canvas: The prediction will be texted on the canvas.
            frame: The image contains posture to be watched.

        Returns:
            The PostureLabel and the detail string of the determination.
        """
        im: GrayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        im = cv2.resize(im, ModelTrainer.IMAGE_DIMENSIONS)
        im = im / 255  # Normalize the image
        im = im.reshape(1, *ModelTrainer.IMAGE_DIMENSIONS, 1)

        # 1 cuz only 1 predict result; 2 cuz there are 2 PostureLabels.
        # e.g, [[8.3688545e-05 9.9991632e-01]]
        predictions: NDArray[(1, 2), Float[32]] = self._model.predict(im)
        # Gets the index which has the greatest confidence value.
        class_pred: Int[64] = numpy.argmax(predictions)
        # Gets the confidence value.
        conf: Float[32] = predictions[0][class_pred]

        detail: str = f"by model: {conf:.0%}"
        cv2.putText(canvas, detail, (15, 110), FONT_0, 0.7, (200, 200, 255), thickness=2)

        return (PostureLabel.GOOD if class_pred == PostureLabel.GOOD.value else PostureLabel.SLUMP), detail
