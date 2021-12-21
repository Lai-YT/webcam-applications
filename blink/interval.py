from enum import Enum, auto
from typing import Tuple

from PyQt5.QtCore import QObject, pyqtSignal

from util.sliding_window import DoubleTimeWindow, WindowType
from util.time import get_current_time


class IntervalLevel(Enum):
    BAD = auto()
    GOOD = auto()


class BlinkRateIntervalDetector(QObject):
    """Splits the times into intervals using the technique of sliding window.
    Detects whether each interval forms a good interval or not; if not, make it
    a bad interval.

    The number of blinks per minute is the blink rate, which is an integer here
    since it counts but does not take the average.

    Signals:
        s_interval_detected:
    """

    s_interval_detected = pyqtSignal(WindowType, int, int, int)  # start, end, rate

    def __init__(self, good_rate_range: Tuple[int, int] = (15, 25)) -> None:
        """
        Arguments:
            good_rate_range:
                The min and max boundary of the good blink rate (blinks per minute).
                It's not about the average rate, so both are with type int.
                15 ~ 25 in default. For a proper blink rate, one may refer to
                https://pubmed.ncbi.nlm.nih.gov/11700965/#affiliation-1
        """
        super().__init__()
        self._good_rate_range = good_rate_range
        self._blink_times = DoubleTimeWindow(60)
        self._blink_times.set_time_catch_callback(self._check_blink_rate)

    def add_blink(self) -> None:
        """Adds a new time of blink and checks whether there's a good interval.

        Emits:
            s_interval_detected:
        """
        self._blink_times.append_time()
        self.check_blink_rate()

    def check_blink_rate(self) -> None:
        """Checks whether there's a good interval and catch up with the current
        time.

        Call this method manually to have the detector follow the current time.
        Emits:
            s_interval_detected:
        """
        self._blink_times.catch_up_time(manual=True)

    def clear_windows(self, *args: WindowType) -> None:
        self._blink_times.clear(*args)

    def _check_blink_rate(self) -> None:
        """
        Emits:
            s_interval_detected:
        """
        curr_time: int = get_current_time()
        if self._blink_times and (curr_time - self._blink_times[0]) >= 60:
            blink_rate: int = self._get_blink_rate(WindowType.CURRENT)
            if self._good_rate_range[0] <= blink_rate <= self._good_rate_range[1]:
                # Emit previous part first since its earlier on time.
                if (self._blink_times.previous
                        and self._blink_times[0] - self._blink_times.previous[0] >= 30):
                    self.s_interval_detected.emit(WindowType.PREVIOUS,
                                                  self._blink_times.previous[0],
                                                  self._blink_times[0],
                                                  self._get_blink_rate(WindowType.PREVIOUS))
                self.s_interval_detected.emit(WindowType.CURRENT,
                                              self._blink_times[0],
                                              self._blink_times[0] + 60,
                                              blink_rate)
        elif (self._blink_times.previous
                and (curr_time - 60) - self._blink_times.previous[0] >= 60):
            self.s_interval_detected.emit(WindowType.PREVIOUS,
                                          self._blink_times.previous[0],
                                          curr_time - 60,
                                          self._get_blink_rate(WindowType.PREVIOUS))

    def _get_blink_rate(self, type: WindowType) -> int:
        """Returns the blink rate of the corresponding window.

        Arguments:
            type: The window to get blink rate from.
        """
        # Since the width of window is 60 seconds, its length is exactly the
        # blink rate.
        blink_rate: int
        if type is WindowType.CURRENT:
            blink_rate = len(self._blink_times)
        elif type is WindowType.PREVIOUS:
            blink_rate = len(self._blink_times.previous)
        return blink_rate