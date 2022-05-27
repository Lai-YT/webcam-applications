import time


# often-used define constants
ONE_MIN = 60
HALF_MIN = 30


class Timer:
    """
    This class makes the measurement of running time easy.
    Simply using start, pause and reset to time your program.
    """

    def __init__(self) -> None:
        self._start: int = 0
        self._pause_start: int = 0
        self._pause_duration: int = 0

    def start(self) -> None:
        """Start counting.

        No effects when the Timer is already started and not paused.
        """
        if self.is_paused():
            self._pause_duration += get_current_time() - self._pause_start
            self._pause_start = 0
        elif self._start == 0:
            self._start = get_current_time()

    def pause(self) -> None:
        """Stop the time count.

        No effects when the Timer is already paused.
        """
        if not self.is_paused():
            self._pause_start = get_current_time()

    def reset(self) -> None:
        """Reset the Timer."""
        self._start = 0
        self._pause_start = 0
        self._pause_duration = 0

    def time(self) -> int:
        """Returns the time count in seconds."""
        # Doesn't even started.
        if self._start == 0:
            return 0
        if self.is_paused():
            return self._pause_start - self._start - self._pause_duration
        return get_current_time() - self._start - self._pause_duration

    def is_paused(self) -> bool:
        """Returns True if the Timer is paused, otherwise False."""
        return self._pause_start != 0


def get_current_time() -> int:
    """Returns the time in seconds since the epoch with the precision up to
    1 second.
    """
    return int(time.time())


def min_to_sec(time_in_min: int) -> int:
    """Simple minute to second conversion method without any check."""
    return time_in_min * 60


def to_date_time(epoch_time: int) -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(epoch_time))
