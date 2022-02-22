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
        self._time_catch_callback: Optional[Callable[[], Any]] = None

    def set_time_catch_callback(
            self,
            time_catch_callback: Callable[[], Any]) -> None:
        """
        Arguments:
            time_catch_callback: Called after the window catches up the time.
        """
        self._time_catch_callback = time_catch_callback

    def append_time(self) -> None:
        """Appends the current time to the window."""
        self._window.append(get_current_time())
        self.catch_up_with_current_time()

    def catch_up_with_current_time(self) -> None:
        """Pops out the earliest time record until the window catches up with
        the current time (doesn't exceed the time_width), then calls the
        time_catch_callback if it's set.
        """
        while self._window_overfilled():
            self._window.popleft()

        self._call_time_catch_callback_if_has()

    def clear(self) -> None:
        """Removes all times from the window."""
        self._window.clear()

    def _window_overfilled(self) -> bool:
        return self._width_of_window() > self._time_width

    def _width_of_window(self) -> int:
        if not self._window:
            return 0
        return get_current_time() - self._window[0]

    def _call_time_catch_callback_if_has(self) -> None:
        if self._has_time_catch_callback():
            self._time_catch_callback()  # type: ignore
                                         # Nullity already checked above.

    def _has_time_catch_callback(self) -> bool:
        return self._time_catch_callback is not None

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


class DoubleTimeWindow(TimeWindow):
    """Instead of simply maintains a current window, this object also keeps the
    previous window, so is named double time.

    Note that one may treat this class as the single TimeWindow since all special
    methods work with the current window only. To work with the previous window,
    call the previous property.
    """
    # Override
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
                e.g., A DoubleTimeWindow with time_width=60 knows the latest 120
                seconds, but one may operate separatly on the 0 ~ 60 and 61 ~ 120
                part.
        """
        super().__init__(time_width)
        self._prev_window: Deque[int] = deque()

    # Override
    def catch_up_with_current_time(self) -> None:
        """Pops out the earliest time record until the window catches up with
        the current time (doesn't exceed the time_width), then calls the
        time_catch_callback if it's set.
        """
        while self._window_overfilled():
            self._prev_window.append(self._window.popleft())

        while self._prev_window_overfilled():
            self._prev_window.popleft()

        self._call_time_catch_callback_if_has()

    @property
    def previous(self) -> Deque[int]:
        """Returns the previous time window."""
        return self._prev_window.copy()

    # Override
    def clear(self, window_type: Optional[WindowType] = None) -> None:
        """Clears the corresponding type of window.

        Arguments:
            window_type:
                If not specified, both current and previous window are cleared.
        """
        if window_type in (WindowType.CURRENT, None):
            super().clear()
        if window_type in (WindowType.PREVIOUS, None):
            self._prev_window.clear()

    def _prev_window_overfilled(self) -> bool:
        return self._width_of_prev_window() > self._time_width

    def _width_of_prev_window(self) -> int:
        if not self._prev_window:
            return 0
        return get_current_time() - self._time_width - self._prev_window[0]

    # Override
    def __str__(self) -> str:
        return ("DoubleTimeWindow{previous"
                + str(self._prev_window).lstrip("deque") + ", "
                + str(self._window).lstrip("deque")
                + "}")
