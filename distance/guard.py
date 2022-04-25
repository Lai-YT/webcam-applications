from enum import Enum, auto
from typing import Optional, Tuple

from nptyping import Int, NDArray

from concentration.grader import ConcentrationGrader
from distance.calculator import DistanceCalculator
from sounds.sound_guard import SoundRepeatGuard
from util.path import to_abs_path


class DistanceState(Enum):
    """
    Two states represent two different relationships
    between distance and limit.
    """
    NORMAL  = auto()
    WARNING = auto()


class DistanceGuard(SoundRepeatGuard):
    """DistanceGuard checks whether the face obtained by the landmarks are at
    a short distance.
    """

    def __init__(
            self,
            calculator: DistanceCalculator,
            warn_dist: float,
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
        super().__init__(
            sound_file=to_abs_path("sounds/too_close.wav"),
            interval=8,
            warning_enabled=warning_enabled
        )
        self._calculator: DistanceCalculator = calculator
        self._warn_dist: float = warn_dist
        self._grader: Optional[ConcentrationGrader] = grader

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

    def warn_if_too_close(
            self,
            landmarks: NDArray[(68, 2), Int[32]]) -> Tuple[float, DistanceState]:
        """Returns the distance and the state of it, also plays the warning
        sound when the distance is less than warn_dist if enabled.

        Arguments:
            landmarks: (x, y) coordinates of the 68 face landmarks.
        """
        distance: float = self._calculator.calculate(landmarks)

        self._repeat_sound_if(distance < self._warn_dist)

        # default state
        state = DistanceState.NORMAL
        if distance < self._warn_dist:
            state = DistanceState.WARNING

        self._send_concentration_info(distance)

        return distance, state

    def _send_concentration_info(self, distance: float) -> None:
        """Sends a distraction to the grader if the distance is too far,
        a concentration otherwise.

        Does nothing if the grader isn't provided.

        Arguments:
            distance: The distance to send info about.
        """

        TOO_FAR = 80
        if self._grader is not None:
            if distance > TOO_FAR:
                self._grader.add_body_distraction()
            else:
                self._grader.add_body_concentration()
