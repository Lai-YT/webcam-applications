from typing import List, Tuple

from PyQt5.QtCore import QObject, pyqtSignal

from concentration.interval import IntervalType
from util.sliding_window import DoubleTimeWindow, TimeWindow, WindowType
from util.time import get_current_time


class FaceExistenceRateCounter(QObject):
    """Everytime a new frame is refreshed, there may exist a face or not. Count
    the existence within 1 minute and simply get the existence rate.

    Signals:
        s_low_existence_detected:
            Emits when face existence is low and sends start and end time.
    """

    s_low_existence_detected = pyqtSignal(int, int)

    def __init__(self, low_existence: float = 0.66) -> None:
        """
        Arguments:
            low_existence:
                Ratio of face over frame lower then this indicates a low face
                existence. 0.66 (2/3) in default.
        """
        super().__init__()
        self._low_existence = low_existence
        self._face_times = TimeWindow(60)
        # it's enough to only set callback on frame
        self._frame_times = TimeWindow(60)
        self._frame_times.set_time_catch_callback(self._check_face_existence)

    @property
    def low_existence(self) -> float:
        """Returns the threshold rate of low face existence."""
        return self._low_existence

    def add_frame(self) -> None:
        """Adds a frame count and detects whether face existence is low.

        Emits:
            s_low_existence_detected:
                Emits when face existence is low and sends the face existence rate.
        """
        self._frame_times.append_time()
        # But also the face time needs to have the same window,
        # so we don't get the wrong value when _get_face_existence_rate().
        self._face_times.catch_up_time(manual=True)

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
        # Frame time is added every frame but face isn't,
        # so is used as the prerequisite for face existence check.
        if (self._frame_times
                and get_current_time() - self._frame_times[0] >= 60
                and self._get_face_existence_rate() <= self._low_existence):
            self.s_low_existence_detected.emit(self._frame_times[0],
                                               self._frame_times[0] + 60)

    def _get_face_existence_rate(self) -> float:
        """Returns the face existence rate of the minute.

        The rate is rounded to two decimal places.

        Notice that this method doesn't check the time and width of both
        windows. ZeroDivisionError may occur when called right after a clear.
        """
        return round(len(self._face_times) / len(self._frame_times), 2)


class BlinkRateIntervalDetector(QObject):
    """Splits the times into intervals using the technique of sliding window.
    Detects whether each interval forms a good interval or not; if not, make it
    a bad interval.

    The number of blinks per minute is the blink rate, which is an integer here
    since it counts but does not take the average.

    Signals:
        s_interval_detected:
    """
    s_interval_detected = pyqtSignal(IntervalType, int, int, int)  # start, end, rate

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
        self._last_interval_end: int = get_current_time()

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
        self._blink_times.catch_up_time(manual=True)

    def clear_windows(self, *args: WindowType) -> None:
        self._blink_times.clear(*args)
        # They are placed here since the interval detector itself know nothing
        # about other grading components, such as FaceExistenceRateCounter.
        #
        # Check previous first since when they are both passed,
        # current takes the lead.
        if WindowType.PREVIOUS in args:
            self._last_interval_end = get_current_time() - 60
        if WindowType.CURRENT in args:
            self._last_interval_end = get_current_time()

    def _check_blink_rate(self) -> None:
        """
        Emits:
            s_interval_detected:
        """
        curr_time: int = get_current_time()
        # When the current window forms a good interval, we should also look
        # back if it's long enough.
        if self._blink_times and (curr_time - self._blink_times[0]) >= 60:
            blink_rate: int = self._get_blink_rate(WindowType.CURRENT)
            if self._good_rate_range[0] <= blink_rate <= self._good_rate_range[1]:
                # Emit previous part first since its earlier on time.
                self._check_blink_rate_of_previous_window(self._blink_times[0], 30)
                self.s_interval_detected.emit(IntervalType.REAL_TIME,
                                              self._blink_times[0], curr_time,
                                              blink_rate)
        # The current window hasn't form a good intervals yet, make each 60
        # seconds of the previous a look back interval.
        else:
            self._check_blink_rate_of_previous_window(curr_time - 60, 60)

    def _check_blink_rate_of_previous_window(self, end: int, width: int) -> None:
        """
        Start time is the end time of the last interval.

        Emits:
            s_interval_detected:
        """
        if end - self._last_interval_end >= width:
            self.s_interval_detected.emit(IntervalType.LOOK_BACK,
                                          self._last_interval_end, end,
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


class BodyConcentrationCounter:
    def __init__(self) -> None:
        self._concentration_times = DoubleTimeWindow(60)
        self._distraction_times = DoubleTimeWindow(60)

    def add_concentration(self) -> None:
        self._concentration_times.append_time()

    def add_distraction(self) -> None:
        self._distraction_times.append_time()

    def get_concentration_ratio(
            self,
            type: WindowType,
            start_time: int,
            end_time: int) -> float:
        """Returns the amount of body concentration in range
        [start_time, end_time], those outsides are trimmed off.

        The result is rounded to two decimal places.

        Arguments:
            type: The window to get concentration from.
            start_time: The start time of the wanted interval.
            end_time: The end time of the wanted interval.
        """
        def count_time_in_interval(times: DoubleTimeWindow) -> int:
            """To avoid un-fully mathced windows between grading components,
            trimmed off the outsides.
            """
            # Convert the window to list so won't be mutated by other threads
            # while iterating.
            window: List[int]
            if type is WindowType.PREVIOUS:
                window = list(times.previous)
            else:
                window = list(times)
            # Iterate through the entire window causes more time;
            # count all then remove out-of-ranges to provide slightly better
            # efficiency.
            count: int = len(window)
            for t in window:
                if t > start_time:
                    break
                count -= 1
            for t in reversed(window):
                if t < end_time:
                    break
                count -= 1
            return count
        concent_count: int = count_time_in_interval(self._concentration_times)
        distract_count: int = count_time_in_interval(self._distraction_times)
        return round(concent_count / (concent_count + distract_count), 2)

    def clear_windows(self, *args: WindowType) -> None:
        """Clears the corresponding windows.

        Arguments:
            args: Various amount of window types.
        """
        self._distraction_times.clear(*args)
        self._concentration_times.clear(*args)
