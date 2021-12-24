import logging
from typing import Deque, List, Optional, Tuple, Union

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from nptyping import Int, NDArray

import concentration.fuzzy.parse as parse
import util.logger as logger
from blink.detector import AntiNoiseBlinkDetector
from blink.interval import BlinkRateIntervalDetector, IntervalLevel
from concentration.fuzzy.classes import Grade, Interval
from concentration.fuzzy.grader import FuzzyGrader
from util.path import to_abs_path
from util.sliding_window import DoubleTimeWindow, TimeWindow, WindowType
from util.time import get_current_time, to_date_time


interval_logger: logging.Logger = logger.setup_logger("interval_logger",
                                                      to_abs_path("concent_interval.log"),
                                                      logging.DEBUG)

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
        automatically called by add_face() and add_frame().
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


class ConcentrationGrader(QObject):

    s_concent_interval_refreshed = pyqtSignal(IntervalLevel, int, int, float)  # start, end, grade

    def __init__(
            self,
            ratio_threshold: float = 0.24,
            consec_frame: int = 3,
            good_rate_range: Tuple[int, int] = (1, 21),
            low_existence: float = 0.66) -> None:
        """
        Arguments:
            ratio_threshold:
                The eye aspect ratio to indicate blink. 0.24 in default.
                It's passed to the underlaying AntiNoiseBlinkDetector.
            consec_frame:
                The number of consecutive frames the eye must be below the threshold
                to indicate a blink. 3 in default.
                It's passed to the underlaying AntiNoiseBlinkDetector.
            good_rate_range:
                The min and max boundary of the good blink rate (blinks per minute).
                It's not about the average rate, so both are with type int.
                1 ~ 21 in default. For a proper blink rate, one may refer to
                https://pubmed.ncbi.nlm.nih.gov/11700965/#affiliation-1
                It's passed to the underlaying BlinkRateIntervalDetector.
            low_existence:
        """
        super().__init__()
        interval_logger.info("ConcentrationGrader configs:")
        interval_logger.info(f" ratio thres  = {ratio_threshold}")
        interval_logger.info(f" consec frame = {consec_frame}")
        interval_logger.info(f" good range   = {good_rate_range}\n")

        self._body_concentration_times = DoubleTimeWindow(60)
        self._body_distraction_times = DoubleTimeWindow(60)
        # TODO: Blink detection not accurate, lots of false blink.
        self._blink_detector = AntiNoiseBlinkDetector(ratio_threshold, consec_frame)
        self._interval_detector = BlinkRateIntervalDetector(good_rate_range)
        self._face_existence_counter = FaceExistenceRateCounter(low_existence)
        self._fuzzy_grader = FuzzyGrader()

        self._json_file: str = to_abs_path("intervals.json")
        parse.init_json(self._json_file)

        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)
        self._interval_detector.s_interval_detected.connect(self.check_normal_concentration)
        self._face_existence_counter.s_low_existence_detected.connect(self.check_low_face_concentration)
        # The refreshment of frame check is fast, clear it immediately to avoid
        # crash due to double check and ZeroDivisionError.
        self._face_existence_counter.s_low_existence_detected.connect(self._face_existence_counter.clear_windows)

        self._check_guard = DuplicateCheckGuard()

    def get_ratio_threshold(self) -> float:
        """Returns the ratio threshold used to consider an EAR lower than it
        to be a blink with noise."""
        return self._blink_detector.ratio_threshold

    def set_ratio_threshold(self, threshold: float) -> None:
        """
        Arguments:
            threshold:
                An eye aspect ratio lower than this is considered to be a blink
                with noise.
        """
        self._blink_detector.ratio_threshold = threshold

    def detect_blink(self, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        self._blink_detector.detect_blink(landmarks)

    def add_frame(self) -> None:
        self._face_existence_counter.add_frame()
        # Basicly, add_frame() is called every frame,
        # so call method which should be called manually together.
        self._interval_detector.check_blink_rate()

    def add_face(self) -> None:
        self._face_existence_counter.add_face()

    def add_body_concentration(self) -> None:
        self._body_concentration_times.append_time()

    def add_body_distraction(self) -> None:
        self._body_distraction_times.append_time()

    def get_body_concentration_grade(
            self,
            type: WindowType,
            start_time: int,
            end_time: int) -> float:
        """Returns the amount of body concentration over total count.

        The result is rounded to two decimal places.
        """
        def count_time_in_interval(times: DoubleTimeWindow) -> int:
            window: Union[DoubleTimeWindow, Deque[int]] = times
            if type is WindowType.PREVIOUS:
                window = times.previous
            # Iterate through the entire window causes more time;
            # count all then remove out-of-ranges to provide slightly better efficiency.
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

        concent_count: int = count_time_in_interval(self._body_concentration_times)
        distract_count: int = count_time_in_interval(self._body_distraction_times)
        return round(concent_count / (concent_count + distract_count), 2)


    @pyqtSlot(WindowType, int, int, int)
    def check_normal_concentration(
            self,
            type: WindowType,
            start_time: int,
            end_time: int,
            blink_rate: int) -> None:
        if self._check_guard.is_blocked((start_time, end_time)):
            interval_logger.info(f"conflict at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
            return
        self._check_guard.block((start_time, end_time))
        interval_logger.info("in check at normal")

        interval_logger.info(f"Check at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
        try:
            body_concent: float = self.get_body_concentration_grade(type, start_time, end_time)
            interval_logger.info(f"body concentration = {body_concent}")
            interval_logger.info(f"blink rate = {blink_rate}")

            grade: float = self._fuzzy_grader.compute_grade(blink_rate, body_concent)
            if type is WindowType.PREVIOUS:
                grade = self._fuzzy_grader.compute_grade(
                    (blink_rate * 60) / (end_time - start_time), body_concent)
                # A grading from the previous can only be bad, since they didn't
                # pass when they were current.
                self.s_concent_interval_refreshed.emit(
                    IntervalLevel.BAD, start_time, end_time, grade)
                parse.append_to_json(
                    self._json_file,
                    Interval(start=start_time, end=end_time, grade=grade).__dict__)
                self.clear_windows(WindowType.PREVIOUS)
                interval_logger.info(f"bad concentration: {grade}")
            elif grade >= 0.6:
                self.s_concent_interval_refreshed.emit(
                    IntervalLevel.GOOD, start_time, end_time, grade)
                parse.append_to_json(
                    self._json_file,
                    Interval(start=start_time, end=end_time, grade=grade).__dict__)
                # The grading of previous should precede current, so after the
                # grading of current, we should and must clear previous also.
                self.clear_windows(WindowType.PREVIOUS, WindowType.CURRENT)
                interval_logger.info(f"good concentration: {grade}")
            else:
                interval_logger.info(f"{grade}, not concentrating")
        except ZeroDivisionError:
            interval_logger.info(f"broken at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
            print(f"broken at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
        finally:
            self._check_guard.release()
            interval_logger.info(f"leave check of normal {to_date_time(start_time)} ~ {to_date_time(end_time)}")
            interval_logger.info("")  # separation

    @pyqtSlot(int, int)
    def check_low_face_concentration(self, start_time: int, end_time: int) -> None:
        """
        Note that no matter good or bad, the low face interval is always graded
        currently.
        """
        if self._check_guard.is_blocked((start_time, end_time)):
            interval_logger.info(f"conflict at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
            return
        self._check_guard.block((start_time, end_time))
        interval_logger.info("in check at low face")

        interval_logger.info(f"Check at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
        interval_logger.info("low face existence, check body only:")

        # low face existence check is always on the current window
        body_concent: float = self.get_body_concentration_grade(
            WindowType.CURRENT, start_time, end_time)
        grade: float = body_concent

        level = IntervalLevel.GOOD if grade >= 0.6 else IntervalLevel.BAD
        self.s_concent_interval_refreshed.emit(level, start_time, end_time, grade)
        parse.append_to_json(
            self._json_file,
            Interval(start=start_time, end=end_time, grade=grade).__dict__
        )
        self.clear_windows(WindowType.CURRENT)

        interval_logger.info(f"concentration: {grade}")
        self._check_guard.release()
        interval_logger.info(f"leave check of low face {to_date_time(start_time)} ~ {to_date_time(end_time)}")
        interval_logger.info("")  # separation

    def clear_windows(self, *args: WindowType) -> None:
        self._body_distraction_times.clear(*args)
        self._body_concentration_times.clear(*args)
        self._interval_detector.clear_windows(*args)

        if WindowType.CURRENT in args:
            self._face_existence_counter.clear_windows()


class DuplicateCheckGuard:
    def __init__(self) -> None:
        self._block: bool = False
        self._interval_to_block: Tuple[int, int] = (0, 0)

    def block(self, interval: Tuple[int, int]) -> None:
        """Blocks the designated interval, which means one will get a True when
        calling an is_blocked() on a intervals that overlaps.
        """
        self._block = True
        self._interval_to_block = interval

    def release(self) -> None:
        """Releases the guard so no interval is blocked."""
        self._block = False

    def is_blocked(self, interval: Tuple[int, int]) -> bool:
        """Returns whether the interval overlaps with the interval to block."""
        return self._block and is_overlapped(interval, self._interval_to_block)



def is_overlapped(interval_1: Tuple[int, int], interval_2: Tuple[int, int]) -> bool:
    """Returns True if the intervals overlapped with each other.

    Both ends of the intervals are considered to be opened.

    Arguments:
        interval_1, interval_2: The 2 intervals to check overlapping on.
    """
    return ((interval_1[0] >= interval_2[0] and not interval_1[0] >= interval_2[1])
            or (interval_1[1] <= interval_2[1] and not interval_1[1] <= interval_2[0]))
