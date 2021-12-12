import time
from abc import ABC, abstractmethod
from collections import deque
from typing import Deque, Optional


from PyQt5.QtCore import QObject


class SlidingWindowHandler(QObject):
    """The user may decide when to clear the windows for a new start."""
    @abstractmethod
    def clear_windows(self) -> None:
        pass


# TODO: TimeWindow and DoubleTimeWindow not ready yet
class TimeWindow:
    def __init__(self, time_length: int = 60) -> None:
        self._window: Deque[int] = deque()
        self._time_length = time_length

    def append_time(self) -> None:
        self._window.append(int(time.time()))
        while self._window and self._window[-1] - self._window[0] > self._time_length:
            self._window.popleft()

    def clear(self) -> None:
        self._window.clear()

    @property
    def front(self) -> int:
        if not self._window:
            raise IndexError("the window is empty")
        return self._window[0]

    @property
    def back(self) -> int:
        if not self._window:
            raise IndexError("the window is empty")
        return self._window[-1]

    def __str__(self) -> str:
        return "TimeWindow" + self._window.__str__().lstrip("deque")

    def __len__(self) -> int:
        return self._window.__len__()


class DoubleTimeWindow:
    """Instead of simply maintain a window, this object also keeps the previous
    window, so is named double time.

    i.g., A DoubleTimeWindow with time_length=60 knows the latest 120 seconds,
    but one may operate separatly on the 0 ~ 60 and 61 ~ 120 part.
    """
    def __init__(self, time_length: int = 60) -> None:
        self._window: Deque[int] = deque()
        self._pre_window: Deque[int] = deque()
        self._time_length = time_length

    def append(self, time: int) -> None:
        self._window.append(time)
        while self._window and self._window[-1] - self._window[0] > self._time_length:
            self._pre_window.append(self._window.popleft())
        while self._pre_window and self._pre_window[-1] - self._pre_window[0] > self._time_length:
            self._pre_window.popleft()

    def clear(self) -> None:
        self._window.clear()
        self._pre_window.clear()


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
