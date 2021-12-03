from abc import ABC, abstractmethod
from typing import Deque, Optional


from PyQt5.QtCore import QObject


class SlidingWindowHandler(QObject):
    """The user may decide when to clear the windows for a new start."""
    @abstractmethod
    def clear_windows(self) -> None:
        pass


def keep_sliding_window_in_one_minute(window: Deque[int], reference_time: Optional[int] = None) -> None:
    """Compares reference time and the earliest time stamp in the window, keep them within a minute.

    Arguments:
        window: The time stamps. Should be sorted in ascending order with respect to time.
        reference_time:
            The time to compare with. If is not provided, the latest time stamp
            in the window is use.
    """
    if reference_time is None:
        reference_time = window[-1]
    while window and reference_time - window[0] > 60:
        window.popleft()
