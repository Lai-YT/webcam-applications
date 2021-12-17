import time
from abc import ABC, abstractmethod
from collections import deque
from typing import Any, Callable, Deque, Optional


from PyQt5.QtCore import QObject


class SlidingWindowHandler(QObject):
    """The user may decide when to clear the windows for a new start."""
    @abstractmethod
    def clear_windows(self) -> None:
        pass


class TimeWindow:
    def __init__(self, time_width: int = 60) -> None:
        """
        Arguments:
            time_width:
                The time width of a window is it's
                    latest time - the earliest time.
                This is the max width of the window, in seconds, 60 in default.
                Times are poped out from the earliest when exceeds.
        """
        self._window: Deque[int] = deque()
        self._time_width = time_width

    def set_time_catch_callback(self, time_catch_callback: Callable[[], Any]) -> None:
        """
        Arguments:
            time_catch_callback: Called before the window catches up the time.
        """
        self._time_catch_callback = time_catch_callback

    def append_time(self) -> None:
        """Appends the current time to the window and catches up the time."""
        self._window.append(int(time.time()))
        self.catch_up_time()

    def catch_up_time(self, *, manual: bool = False) -> None:
        """Calls the time_catch_callback if it's set, then pop out the oldest
        time record until the window catches up with the time (doesn't exceed
        the time_width).

        This method does nothing if the window is empty.

        Arguments:
            manual:
                If manual is True, the time to catch up with is the current time,
                otherwise with the latest time in the window. False in default.
        """
        if not self._window:
            return

        if hasattr(self, "_time_catch_callback"):
            self._time_catch_callback()
        # the time to catch up with
        time_ = self._window[-1]
        if manual:
            time_ = int(time.time())
        # catch up
        while self._window and time_ - self._window[0] > self._time_width:
            self._window.popleft()

    def clear(self) -> None:
        """Removes all times from the window."""
        self._window.clear()

    def __getitem__(self, index: int) -> int:
        """Returns the index-th earliest time in the window.

        Notice that the earliest time is with index 0.
        """
        return self._window[index]

    def __len__(self) -> int:
        """Returns how many time records there are in the window."""
        return len(self._window)

    def __str__(self) -> int:
        return "TimeWindow" + str(self._window).lstrip("deque")

# TODO: DoubleTimeWindow not ready yet
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
