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


class TimeWindow(deque):
    def __init__(self, width: int = 60) -> None:
        """
        Arguments:
            width:
                The width of the time window, in seconds, 60 in default.
                Pops out from the earliest when time exceeds.
        """
        super().__init__()
        self._width = width

    def set_time_catch_callback(self, time_catch_callback: Callable[[], Any]) -> None:
        """
        Arguments:
            time_catch_callback: Called before the window catches up the time.
        """
        self._time_catch_callback = time_catch_callback

    def append_time(self) -> None:
        """Appends the current time to the window and catches up the time."""
        super().append(int(time.time()))
        self.catch_up_time()

    def catch_up_time(self, *, manual: bool = False) -> None:
        """Calls the time_catch_callback if it's set, then pop out the oldest
        time record until the window catches up with the time (doesn't exceed
        the width).

        This method does nothing if the window is empty.

        Arguments:
            manual:
                If manual is True, the time to catch up with is the current time,
                otherwise with the latest time in the window. False in default.
        """
        if not super().__len__():
            return

        if hasattr(self, "_time_catch_callback"):
            self._time_catch_callback()
        # the time to catch up with
        time_ = super().__getitem__(-1)
        if manual:
            time_ = int(time.time())
        # catch up
        while (super().__len__()
                and time_ - super().__getitem__(0) > self._width):
            super().popleft()

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
