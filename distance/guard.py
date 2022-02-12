from enum import Enum, auto
from typing import Optional

import cv2
from PyQt5.QtCore import QObject, pyqtSignal
from nptyping import Int, NDArray
from playsound import playsound

from concentration.grader import ConcentrationGrader
from distance.calculator import DistanceCalculator
from util.color import MAGENTA, RED
from util.cv_font import FONT_0
from util.image_type import ColorImage
from util.path import to_abs_path
from util.time import Timer


class DistanceState(Enum):
    """
    Two states represent two different relationships
    between distance and limit.
    """
    NORMAL  = auto()
    WARNING = auto()


class DistanceGuard(QObject):
    """DistanceGuard checks whether the face obtained by the landmarks are at
    a short distance.

    Signals:
        s_distance_refreshed: Emits everytime a new distance is calculated.
    """

    s_distance_refreshed = pyqtSignal(float, DistanceState)

    def __init__(self,
                 calculator: Optional[DistanceCalculator] = None,
                 warn_dist: Optional[float] = None,
                 warning_enabled: bool = True,
                 grader: Optional[ConcentrationGrader] = None) -> None:
        """
        Arguments:
            calculator: Use to calculate the distance between face and screen.
            warn_dist : Distance closer than this is to be warned.
            warning_enabled:
                Whether there's sound that warns the user when the distance is
                too close. Enabled in default.
            grader:
                Provide this optional argument if you're using the guard as
                one of the overall concentration grading components. The result
                will be send to the grader.
        """
        super().__init__()

        self._calculator: Optional[DistanceCalculator] = calculator
        self._warn_dist: Optional[float] = warn_dist
        self._grader: Optional[ConcentrationGrader] = grader
        self._warning_enabled: bool = warning_enabled

        self._wavfile: str = to_abs_path("sounds/too_close.wav")
        self._warning_repeat_timer = Timer()
        # To avoid double play due to a near time check (less than 1 sec).
        self._f_played: bool = False

    def set_calculator(self, calculator: DistanceCalculator) -> None:
        """
        Arguments:
            calculator: Use to calculate the distance between face and screen.
        """
        self._calculator = calculator

    def set_warn_dist(self, warn_dist: float) -> None:
        """
        Arguments:
            warn_dist : Distance closer than this is to be warned.
        """
        self._warn_dist = warn_dist

    def set_warning_enabled(self, enabled: bool) -> None:
        """
        Arguments:
            enabled:
                Whether there's sound that warns the user when the distance
                is too close.
        """
        self._warning_enabled = enabled

    def warn_if_too_close(
            self,
            canvas: ColorImage,
            landmarks: NDArray[(68, 2), Int[32]]) -> None:
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
        if self._calculator is None:
            return
        # Distance can be calculated when DistanceCalculator exists.
        if self._calculator is not None:
            distance: float = self._calculator.calculate(landmarks)
            self._put_distance_text(canvas, distance)
        # Has DistanceCalculator but no warn dist.
        # Send the distance with normal state. And no further process.
        if self._warn_dist is None:
            self.s_distance_refreshed.emit(distance, DistanceState.NORMAL)
            return

        # warning logic...
        if self._warning_enabled and distance < self._warn_dist:
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

        self._send_concentration_info(state)

    def _send_concentration_info(self, state: DistanceState) -> None:
        """Sends a concentration to the grader if the state is normal,
        a distraction otherwise.

        Does nothing if the grader isn't provided.

        Arguments:
            state: The state of distance to send info about.
        """
        # TODO: Should too far but not too close be considered as distraction?
        if self._grader is not None:
            if state is DistanceState.NORMAL:
                self._grader.add_body_concentration()
            else:
                self._grader.add_body_distraction()

    def _put_distance_text(self, canvas: ColorImage, distance: float) -> None:
        """Puts distance text on the canvas.

        Distance is rounded to two decimal places.

        Arguments:
            canvas: Imgae to put text on.
            distance: The distance to be put.
        """
        text = "dist. " + str(round(distance, 2))
        cv2.putText(canvas, text, (10, 30), FONT_0, 0.9, MAGENTA, 2)
