import time


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
            self._pause_duration += self._get_time() - self._pause_start
            self._pause_start = 0
        elif self._start == 0:
            self._start = self._get_time()

    def pause(self) -> None:
        """Stop the time count.
        No effects when the Timer is already paused.
        """
        if not self.is_paused():
            self._pause_start = self._get_time()

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
        return self._get_time() - self._start - self._pause_duration

    def is_paused(self) -> bool:
        """Returns True if the Timer is paused, otherwise False."""
        return self._pause_start != 0

    @staticmethod
    def _get_time() -> int:
        return int(time.time())


def min_to_sec(time_in_min: int) -> int:
    """Simple minute to second conversion method without any check."""
    return time_in_min * 60
