from collections import deque
from enum import Enum, auto
from typing import Any, Callable, Deque, Iterator, Optional

from util.time import get_current_time


class TimeWindow:
    """A sliding window that keeps track of the current interval of time."""

    def __init__(self, time_width: int = 60) -> None:
        """
        Arguments:
            time_width:
                The time width of a window is it's
                    latest time - the earliest time.
                This is the max width of the window, in seconds, 60 in default.
                Times are poped out from the earliest when exceeds.

                Notice that the interval is closed, 60 is allowed to keep in a
                window with time width 60.
        """
        self._window: Deque[int] = deque()
        self._time_width = time_width

    def set_time_catch_callback(self, time_catch_callback: Callable[[], Any]) -> None:
        """
        Arguments:
            time_catch_callback: Called after the window catches up the time.
        """
        self._time_catch_callback = time_catch_callback

    def append_time(self) -> None:
        """Appends the current time to the window and catches up the time."""
        self._window.append(get_current_time())
        self.catch_up_time()

    def catch_up_time(self, *, manual: bool = False) -> None:
        """Pops out the earliest time record until the window catches up with the
        time (doesn't exceed the time_width), then calls the time_catch_callback
        if it's set.

        Arguments:
            manual:
                If manual is True, the time to catch up with is the current time,
                otherwise with the latest time in the window. False in default.
        """
        time: int
        if self._window:
            # the time to catch up with
            time_ = self._window[-1]
            if manual:
                time_ = get_current_time()
            # Catch up. Pop out only if "greater" than width.
            while self._window and time_ - self._window[0] > self._time_width:
                self._window.popleft()

        if hasattr(self, "_time_catch_callback"):
            self._time_catch_callback()

    def clear(self) -> None:
        """Removes all times from the window."""
        self._window.clear()

    def __getitem__(self, index: int) -> int:
        """Returns the index-th earliest time in the window.

        Notice that the earliest time is with index 0.
        """
        return self._window[index]

    def __iter__(self) -> Iterator[int]:
        return iter(self._window)

    def __reversed__(self) -> Iterator[int]:
        return reversed(self._window)

    def __len__(self) -> int:
        """Returns how many time records there are in the window."""
        return len(self._window)

    def __str__(self) -> str:
        return "TimeWindow" + str(self._window).lstrip("deque")


class WindowType(Enum):
    """This is a helper enum that helps to indicate which window one is working
    with.
    """
    CURRENT = auto()
    PREVIOUS = auto()


class DoubleTimeWindow:
    """Instead of simply maintain a current window, this object also keeps the
    previous window, so is named double time.

    Note that one may treat this class as the single TimeWindow since all special
    methods work with the current window only. To work with the previous window,
    call the previous property.
    """
    def __init__(self, time_width: int = 60) -> None:
        """
        Arguments:
            time_width:
                The time width of a window is it's
                    latest time - the earliest time.
                This is the max width to each of the 2 windows, in seconds,
                60 in default.
                When the current window is about to slide, it pops out the
                times to the previous window from the earliest; as for the
                previous window, the earliest times are poped and removed.
                Notice that the interval is closed.
                i.g., A DoubleTimeWindow with time_width=60 knows the latest 120
                seconds, but one may operate separatly on the 0 ~ 60 and 61 ~ 120
                part.
        """
        self._window: Deque[int] = deque()
        self._pre_window: Deque[int] = deque()
        self._time_width = time_width

    def append_time(self) -> None:
        """Appends the current time to the window and catches up the time."""
        self._window.append(get_current_time())
        self.catch_up_time()

    def set_time_catch_callback(self, time_catch_callback: Callable[[], Any]) -> None:
        """
        Arguments:
            time_catch_callback: Called after the window catches up the time.
        """
        self._time_catch_callback = time_catch_callback

    def catch_up_time(self, *, manual: bool = False) -> None:
        """Pops out the earliest time record until the window catches up with the
        time (doesn't exceed the time_width), then calls the time_catch_callback
        if it's set.

        Arguments:
            manual:
                If manual is True, the time to catch up with is the current time,
                otherwise with the latest time in the window. False in default.
        """
        time_: int
        if self._window:
            # the time to catch up with
            time_ = self._window[-1]
            if manual:
                time_ = get_current_time()
            # Catch up. Pop out only if "greater" than width.
            while self._window and time_ - self._window[0] > self._time_width:
                self._pre_window.append(self._window.popleft())
        if self._pre_window:
            time_ = self._pre_window[-1]
            if manual:
                time_ = get_current_time() - self._time_width
            # Catch up. Pop out only if "greater" than width.
            while self._pre_window and time_ - self._pre_window[0] > self._time_width:
                self._pre_window.popleft()

        if hasattr(self, "_time_catch_callback"):
            self._time_catch_callback()

    @property
    def previous(self) -> Deque[int]:
        """Returns the previous time window."""
        return self._pre_window

    def clear(self, *args: WindowType) -> None:
        if WindowType.PREVIOUS in args:
            self._pre_window.clear()
        if WindowType.CURRENT in args:
            self._window.clear()

    def __len__(self) -> int:
        return len(self._window)

    def __getitem__(self, index: int) -> int:
        return self._window[index]

    def __iter__(self) -> Iterator[int]:
        return iter(self._window)

    def __reversed__(self) -> Iterator[int]:
        return reversed(self._window)

    def __str__(self) -> str:
        return ("DoubleTimeWindow{previous"
                + str(self._pre_window).lstrip("deque") + ", "
                + str(self._window).lstrip("deque")
                + "}")
