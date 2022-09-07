from collections import deque
from typing import Deque, List, Optional, Tuple

from PyQt5.QtCore import QObject, pyqtSignal
from more_itertools import SequenceView

from concentration.fuzzy.classes import Interval
from concentration.interval import IntervalType
from util.time import HALF_MIN, ONE_MIN, now
from util.time_window import DoubleTimeWindow, TimeWindow, WindowType


class FaceExistenceRateCounter(QObject):
    """Everytime a new frame is refreshed, there may exist a face or not. Count
    the existence within 1 minute and simply get the existence rate.

    Signals:
        s_low_existence_detected:
            Emits when face existence is low and sends its interval.
    """

    s_low_existence_detected = pyqtSignal(Interval)

    def __init__(self, low_existence: float = 0.66) -> None:
        """
        Arguments:
            low_existence:
                Ratio of face over frame lower then this indicates a low face
                existence. 0.66 (2/3) in default.
        """
        super().__init__()
        self._low_existence = low_existence
        self._face_times = TimeWindow(ONE_MIN)
        # it's enough to only set callback on frame
        self._frame_times = TimeWindow(ONE_MIN)
        self._frame_times.set_time_catch_callback(self._check_face_existence)

    def add_frame(self) -> None:
        """Adds a frame count and detects whether face existence is low.

        Emits:
            s_low_existence_detected:
                Emits when face existence is low and sends the face existence rate.
        """
        self._frame_times.append_time()
        # But also the face time needs to have the same window,
        # so we don't get the wrong value when _get_face_existence_rate().
        self._face_times.catch_up_with_current_time()

    def add_face(self) -> None:
        """Adds a face count and detects whether face existence is low.

        Notice that this method should always be called with an add_frame().

        Emits:
            s_low_existence_detected:
                Emits when face existence is low and sends the face existence rate.
        """
        self._face_times.append_time()
        # An add face should always be with an add frame,
        # so we don't need extra synchronization.

    def is_low_face(self) -> bool:
        """Returns True if the counts of the current minute indicates a low
        face interval.

        Notice that this method doesn't really know the minute, only the
        windows. ZeroDivisionError may occur when called right after a clear.
        """
        return self._get_face_existence_rate() <= self._low_existence

    def clear_windows(self) -> None:
        """Clears the time of face and frames in the past 1 minute.

        Call this method manually after a low face existing is detected so the
        faces won't be counted twice and used in the next interval.
        """
        self._face_times.clear()
        self._frame_times.clear()

    def _check_face_existence(self) -> None:
        """Checks whether the face existence is low.

        Note that this method doesn't maintain the sliding window and is
        automatically called by add_frame().

        Emits:
            s_low_existence_detected:
                Emits when face existence is low and sends the start and end time.
        """
        frame_times: SequenceView = self._frame_times.times()
        # Frame time is added every frame but face isn't,
        # so is used as the prerequisite for face existence check.
        if frame_times and now() - frame_times[0] >= ONE_MIN and self.is_low_face():
            self.s_low_existence_detected.emit(
                Interval(frame_times[0], frame_times[0] + ONE_MIN)
            )

    def _get_face_existence_rate(self) -> float:
        """Returns the face existence rate of the minute.

        The rate is rounded to two decimal places.

        Notice that this method doesn't check the time and width of both
        windows. ZeroDivisionError may occur when called right after a clear.
        """
        return round(len(self._face_times) / len(self._frame_times), 2)


class BlinkRateIntervalDetector(QObject):
    """Splits the times into intervals using the technique of sliding window.
    Detects whether an interval forms a good interval or not by blink rate.

    The number of blinks per minute is the blink rate, which is an integer here
    since it counts but does not take the average.

    Signals:
        s_interval_detected:
    """

    s_interval_detected = pyqtSignal(Interval, IntervalType, int)  # rate

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
        self._blink_times = DoubleTimeWindow(ONE_MIN)
        self._blink_times.set_time_catch_callback(self._check_blink_rate)
        self._last_end_time: int = now()

    def add_blink(self) -> None:
        """Adds a new time of blink and checks whether there's a good interval.

        Emits:
            s_interval_detected:
        """
        self._blink_times.append_time()

    def check_blink_rate(self) -> None:
        """Checks whether there's a good interval and catch up with the current
        time.

        Call this method manually to have the detector follow the current time.

        Emits:
            s_interval_detected:
        """
        self._blink_times.catch_up_with_current_time()

    def get_extrude_interval(self) -> Optional[Tuple[Interval, IntervalType, int]]:
        one_min_before: int = now() - ONE_MIN
        # "== ONE_MIN" should be caught as LOOK_BACK
        if HALF_MIN <= (one_min_before - self._last_end_time) < ONE_MIN:
            extrude_interval = (
                Interval(self._last_end_time, one_min_before),
                IntervalType.EXTRUSION,
                self._get_blink_rate(WindowType.PREVIOUS),
            )
            return extrude_interval
        return None

    def clear_windows(self, window_type: WindowType) -> None:
        """Clears the corresponding windows.

        Arguments:
            window_type: The type of window to be cleared.
        """
        self._blink_times.clear(window_type)

    def sync_last_end_up(self, last_end_time: int) -> None:
        """The grader that uses the interval detector should sync the last end
        time up when an interval is graded.
        """
        if last_end_time < self._last_end_time:
            raise ValueError("time shouldn't go backward")
        self._last_end_time = last_end_time

    def _check_blink_rate(self) -> None:
        """Checks whether the current window forms a good blink rate interval
        or the previous window needs a look back.

        Types of REAL_TIME and LOOK_BACK are emitted initiatively during
        the check while EXTRUSION needs a grader to request.

        Emits:
            s_interval_detected:
        """
        now_time: int = now()
        one_min_before: int = now_time - ONE_MIN

        curr_blink_rate: int = self._get_blink_rate(WindowType.CURRENT)
        if (
            now_time - self._last_end_time >= ONE_MIN
            and self._good_rate_range[0] <= curr_blink_rate <= self._good_rate_range[1]
        ):
            self.s_interval_detected.emit(
                Interval(one_min_before, now_time),
                IntervalType.REAL_TIME,
                curr_blink_rate,
            )
        # Make each 60 seconds of the previous a look back interval.
        if one_min_before - self._last_end_time >= ONE_MIN:
            self.s_interval_detected.emit(
                Interval(self._last_end_time, one_min_before),
                IntervalType.LOOK_BACK,
                self._get_blink_rate(WindowType.PREVIOUS),
            )

    def _get_blink_rate(self, window_type: WindowType) -> int:
        """Returns the blink rate of the corresponding window.

        Arguments:
            window_type: The window to get blink rate from.
        """
        # Since the width of window is 60 seconds, its length is exactly the
        # blink rate.
        blink_rate: int
        if window_type is WindowType.CURRENT:
            blink_rate = len(self._blink_times)
        elif window_type is WindowType.PREVIOUS:
            blink_rate = len(self._blink_times.prev_times())
        return blink_rate


class BodyConcentrationCounter:
    """Counts the body concentrations so that the grader can take as an
    criterion, but does not request a grading process, which means the
    BodyConcentrationCounter gives information passively.
    """

    def __init__(self) -> None:
        self._concentration_times = DoubleTimeWindow(ONE_MIN)
        self._distraction_times = DoubleTimeWindow(ONE_MIN)

    def add_concentration(self) -> None:
        self._concentration_times.append_time()

    def add_distraction(self) -> None:
        self._distraction_times.append_time()

    def get_concentration_ratio(self, window_type: WindowType) -> float:
        """Returns the amount of body concentration in the interval.

        The result is rounded to two decimal places.

        Arguments:
            window_type: The window to get concentration from.
        """

        def count_time_in_interval(times: DoubleTimeWindow) -> int:
            # Assumes that the interval is synced up properly, so the count is
            # simply the length of the corresponding window.
            window: SequenceView
            if window_type is WindowType.PREVIOUS:
                window = times.prev_times()
            else:
                window = times.times()
            return len(window)

        concent_count: int = count_time_in_interval(self._concentration_times)
        distract_count: int = count_time_in_interval(self._distraction_times)
        return round(concent_count / (concent_count + distract_count), 2)

    def clear_windows(self, window_type: WindowType) -> None:
        """Clears the corresponding windows.

        Arguments:
            window_type: The type of window to be cleared.
        """
        self._distraction_times.clear(window_type)
        self._concentration_times.clear(window_type)


class FaceCenterCounter:
    # TODO: nearly a duplicated reimplementation of DoubleTimeWindow to carry extra data
    def __init__(self, time_width: int) -> None:
        self._time_width = time_width
        self._face_centers: Deque[Tuple[int, Tuple[float, float]]] = deque()
        self._prev_face_centers: Deque[Tuple[int, Tuple[float, float]]] = deque()

    def add_face_center(self, center: Tuple[float, float]) -> None:
        self._face_centers.append((now(), center))
        self.catch_up_with_current_time()

    def catch_up_with_current_time(self) -> None:
        """Pops out the earliest time record until the window catches up with
        the current time (doesn't exceed the time_width).
        """
        while self._window_overfilled():
            self._prev_face_centers.append(self._face_centers.popleft())

        while self._prev_window_overfilled():
            self._prev_face_centers.popleft()

    def clear_windows(self, window_type: WindowType) -> None:
        if window_type is WindowType.CURRENT:
            self._face_centers.clear()
        if window_type is WindowType.PREVIOUS:
            self._prev_face_centers.clear()

    def current(self) -> List[Tuple[float, float]]:
        return [center for _, center in self._face_centers]

    def previous(self) -> List[Tuple[float, float]]:
        return [center for _, center in self._prev_face_centers]

    def _window_overfilled(self) -> bool:
        return self._width_of_window() > self._time_width

    def _width_of_window(self) -> int:
        if not self._face_centers:
            return 0
        return now() - self._face_centers[0][0]

    def _prev_window_overfilled(self) -> bool:
        return self._width_of_prev_window() > self._time_width

    def _width_of_prev_window(self) -> int:
        if not self._prev_face_centers:
            return 0
        return now() - self._time_width - self._prev_face_centers[0][0]
