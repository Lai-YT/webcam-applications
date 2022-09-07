import time


# often-used define constants
ONE_MIN = 60
HALF_MIN = 30


class Timer:
    """
    This class makes the measurement of running time easy.
    Simply using start, pause and reset to time your program.

    Resolution: integer second
    """

    _UNSET = -1  # time wouldn't be negative, so it's ok

    def __init__(self) -> None:
        self._start_time: int = Timer._UNSET
        self._pause_time: int = Timer._UNSET
        self._pause_duration: int = 0

    def start(self) -> None:
        """
        No effects when the Timer is already started or not paused.
        """
        if self._has_never_started():
            self._start_time = now()
            self._pause_time = Timer._UNSET
        elif self.is_paused():
            self._pause_duration += now() - self._pause_time
            self._pause_time = Timer._UNSET

    def pause(self) -> None:
        """
        No effects when the Timer is already paused or not even started yet.
        """
        if not self.is_paused() and not self._has_never_started():
            self._pause_time = now()

    def reset(self) -> None:
        self._start_time = Timer._UNSET
        self._pause_time = Timer._UNSET
        self._pause_duration = 0

    def time(self) -> int:
        """Returns the time count in seconds."""
        if self._has_never_started():
            return 0
        if self.is_paused():
            return self._pause_time - self._start_time - self._pause_duration
        return now() - self._start_time - self._pause_duration

    def is_paused(self) -> bool:
        return self._pause_time != Timer._UNSET

    def _has_never_started(self) -> bool:
        return self._start_time == Timer._UNSET


def now() -> int:
    """Returns the time in seconds since the epoch with the precision up to
    1 second.
    """
    return int(time.time())


def min_to_sec(time_in_min: int) -> int:
    """Simple minute to second conversion method without any check."""
    return time_in_min * 60


def to_date_time(epoch_time: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_time))
