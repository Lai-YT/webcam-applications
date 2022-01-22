import functools
import time
import logging
from typing import Optional, Tuple

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from nptyping import Int, NDArray

import concentration.fuzzy.parse as parse
from blink.detector import AntiNoiseBlinkDetector
from concentration.criterion import (
    BlinkRateIntervalDetector,
    BodyConcentrationCounter,
    FaceExistenceRateCounter
)
from concentration.fuzzy.classes import Interval
from concentration.fuzzy.grader import FuzzyGrader
from concentration.interval import IntervalType
from util.heap import MinHeap
from util.logger import setup_logger
from util.path import to_abs_path
from util.sliding_window import WindowType
from util.time import ONE_MIN, get_current_time, to_date_time


class ConcentrationGrader(QObject):
    """While grading, there are 3 criteria that we take into account:
    - Blink rate
    - Body concentration, which is the posture
    - Face existence, whether the user is in front of the screen

    Signals:
        s_concent_interval_refreshed:
            Emits when an interval is recorded and sends that interval.
    """
    s_concent_interval_refreshed = pyqtSignal(Interval)

    def __init__(
            self,
            # Passed to the underlaying AntiNoiseBlinkDetector.
            ratio_threshold: float = 0.24,
            # Passed to the underlaying AntiNoiseBlinkDetector.
            consec_frame: int = 3,
            good_rate_range: Tuple[int, int] = (1, 21),
            # Passed to the underlaying FaceExistenceRateCounter.
            low_existence: float = 0.66) -> None:
        """
        Arguments:
            ratio_threshold:
                The eye aspect ratio to indicate blink. 0.24 in default.
            consec_frame:
                The number of consecutive frames the eye must be below the
                threshold to indicate a blink. 3 in default.
            good_rate_range:
                The min and max boundary of the good blink rate (blinks per minute).
                It's not about the average rate, so both are with type int.
                1 ~ 21 in default. For a proper blink rate, one may refer to
                https://pubmed.ncbi.nlm.nih.gov/11700965/#affiliation-1
                It's passed to the underlaying BlinkRateIntervalDetector.
            low_existence:
                Ratio of face over frame lower then this indicates a low face
                existence. 0.66 (2/3) in default.
        """
        super().__init__()
        # Loggings for flow tracing.
        self._grade_logger: logging.Logger = setup_logger(
            "grade_logger", to_abs_path("grades.log"), logging.DEBUG)
        self._grade_logger.info(f"Grader starts at {to_date_time(get_current_time())}\n")

        # FIXME: Blink detection not accurate, lots of false blink.
        self._blink_detector = AntiNoiseBlinkDetector(ratio_threshold, consec_frame)

        self._interval_detector = BlinkRateIntervalDetector(good_rate_range)
        self._interval_detector.s_interval_detected.connect(
            self._push_interval_to_grade_in_heap)
        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)

        # Since the append of blinks is sparse, we need a timer to periodically
        # sync its windows up.
        self._interval_timer = QTimer(self)
        self._interval_timer.timeout.connect(self._interval_detector.check_blink_rate)
        self._interval_timer.start(1_000)

        self._body_concent_counter = BodyConcentrationCounter()

        self._face_existence_counter = FaceExistenceRateCounter(low_existence)
        self._face_existence_counter.s_low_existence_detected.connect(
            functools.partial(self._push_interval_to_grade_in_heap, interval_type=IntervalType.LOW_FACE))

        self._fuzzy_grader = FuzzyGrader()

        # method to record grades
        self._json_file: str = to_abs_path("intervals.json")
        parse.init_json(self._json_file)
        self.s_concent_interval_refreshed.connect(
            lambda interval: parse.append_to_json(self._json_file, interval.__dict__))

        # Min heaps that store the intervals to grade.
        # The curr heap has the REAL_TIME and LOW_FACEs, which are in the current
        # windows; the prev heap has the LOOK_BACKs, which are in the previous.
        self._curr_heap  = MinHeap[Tuple[Interval, IntervalType, Optional[int]]]()
        self._look_backs = MinHeap[Tuple[Interval, IntervalType, int]]()

        # Record the progress of grading time so we don't grade twice.
        self._last_end_time: int = 0

        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._grade_intervals)
        self._process_timer.start(1_000)

    @property
    def ratio_threshold(self) -> float:
        """Returns the ratio threshold used to consider an EAR lower than it
        to be a blink with noise."""
        return self._blink_detector.ratio_threshold

    @ratio_threshold.setter
    def ratio_threshold(self, threshold: float) -> None:
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

    def add_face(self) -> None:
        self._face_existence_counter.add_face()

    def add_body_concentration(self) -> None:
        self._body_concent_counter.add_concentration()

    def add_body_distraction(self) -> None:
        self._body_concent_counter.add_distraction()

    @pyqtSlot(Interval, IntervalType)
    @pyqtSlot(Interval, IntervalType, int)
    def _push_interval_to_grade_in_heap(
            self,
            interval: Interval,
            interval_type: IntervalType,
            # LOW_FACE doesn't have BR
            blink_rate: Optional[int] = None) -> None:
        """
        The one that starts first should be graded first. If the time are the
        same, type with higher priority is graded first.
        """
        heap: MinHeap
        if interval_type is IntervalType.LOOK_BACK:
            heap = self._look_backs
        else:
            heap = self._curr_heap
        heap.push((interval, interval_type, blink_rate))

    def _grade_intervals(self) -> None:
        """Dispatches the intervals to their corresponding grading method."""
        # First, grade the LOOK_BACKs.
        while self._look_backs:
            interval, interval_type, blink_rate = self._look_backs.pop()
            if (not self._is_graded_interval(interval)
                    and self._perform_face_existing_grading(interval, interval_type, blink_rate)):
                self._last_end_time = interval.end
                self._interval_detector.sync_last_end_up(self._last_end_time)
        # Second, grade the REAL_TIME and LOW_FACEs.
        # Additionally grade EXTRUSIONs if existed.
        while self._curr_heap:
            interval, interval_type, blink_rate = self._curr_heap.pop()  # type: ignore
            # Error because of the following reason:
            # Variable reuse within one function body. Mypy really prefers that you don't do that.
            # I decide to ignore and keep clean.
            if self._is_graded_interval(interval):
                continue
            if interval_type is IntervalType.LOW_FACE:
                recorded = self._perform_low_face_grading(interval)
            elif self._face_existence_counter.is_low_face():
                # Not a LOW_FACE interval but is low face. We can expect
                # that there is a LOW_FACE but not yet in the heap.
                # So keep poping util we get the request of LOW_FACE.
                # Note that I assume the time asychronous problem is
                # negligible since it's within a second.
                self._grade_logger.info(
                    f"low face, skip {to_date_time(interval.start)} ~ "
                    f"{to_date_time(interval.end)}, {str(interval_type)}")
                continue
            else:
                recorded = self._perform_face_existing_grading(interval, interval_type, blink_rate)
            if recorded:
                extrude_interval: Optional[Tuple[Interval, IntervalType, int]] = (
                    self._interval_detector.get_extrude_interval())
                if (extrude_interval is not None
                        and not self._is_graded_interval(extrude_interval[0])):
                    self._perform_face_existing_grading(*extrude_interval)
                # unexpected situation, logging...
                if (extrude_interval is not None
                        and self._is_graded_interval(extrude_interval[0])):
                    self._grade_logger.info(str(extrude_interval))
                    self._grade_logger.info(str(self._last_end_time))

                self._last_end_time = interval.end
                self._interval_detector.sync_last_end_up(self._last_end_time)

    def _is_graded_interval(self, interval: Interval) -> bool:
        """Returns whether the interval starts before the last end time.

        Arguments:
            interval: The interval dataclass which contains start and end time.
        """
        return interval.start < self._last_end_time

    def _perform_face_existing_grading(
            self,
            interval: Interval,
            interval_type: IntervalType,
            blink_rate: int) -> bool:
        """Performs grading on the face existing interval and records it
        if the grade is high enough.

        Notice that this method doesn't update the last end time.

        Arguments:
            interval: The interval dataclass which contains start and end time.
            interval_type: The type of such interval.
            blink_rate: The blink rate in that interval.

        Returns:
            True if the grading result is recorded, otherwise False.

        Emits:
            s_concent_interval_refreshed:
                Emits if the the grading result is recorded and sends the grade.
        """
        self._grade_logger.info(f"Normal check at {to_date_time(interval.start)} ~ "
                                f"{to_date_time(interval.end)}")
        self._grade_logger.info(f"blink rate = {blink_rate}")

        window_type = WindowType.CURRENT
        if interval_type in {IntervalType.LOOK_BACK, IntervalType.EXTRUSION}:
            window_type = WindowType.PREVIOUS

        body_concent: float = self._body_concent_counter.get_concentration_ratio(
            window_type, interval)
        self._grade_logger.info(f"body concentration = {body_concent}")

        # LOOK_BACK and EXTRUSIONs are always graded and record.
        if interval_type in {IntervalType.LOOK_BACK, IntervalType.EXTRUSION}:
            if interval_type is IntervalType.LOOK_BACK:
                interval.grade = self._fuzzy_grader.compute_grade(blink_rate, body_concent)
            elif interval_type is IntervalType.EXTRUSION:
                # Use an average-based BR.
                interval.grade = self._fuzzy_grader.compute_grade(
                    (blink_rate*ONE_MIN) / (interval.end-interval.start), body_concent)
            self.s_concent_interval_refreshed.emit(interval)
            self._clear_windows(window_type)
            # A grading on previous can only be bad, since they didn't
            # pass when they were real time.
            self._grade_logger.info(f"bad concentration: {interval.grade}")
            return True
        # REAL_TIMEs
        grade: float = self._fuzzy_grader.compute_grade(blink_rate, body_concent)
        if grade >= 0.6:
            interval.grade = grade
            self.s_concent_interval_refreshed.emit(interval)
            self._clear_windows(window_type)
            self._grade_logger.info(f"good concentration: {interval.grade}")
            return True
        else:
            self._grade_logger.info(f"{grade}, not concentrating")
            return False

    def _perform_low_face_grading(self, interval: Interval) -> bool:
        """Performs grading on the low face existence interval and records it
        if the grade is high enough.

        Notice that this method doesn't update the last end time.

        Arguments:
            interval: The interval dataclass which contains start and end time.

        Returns:
            True if the grading result is recorded, otherwise False.

            Note that this method always records the result and returns True.

        Emits:
            s_concent_interval_refreshed:
                Emits if the the grading result is recorded and sends the grade.
        """
        self._grade_logger.info(f"Low face check at {to_date_time(interval.start)} ~ "
                                f"{to_date_time(interval.end)}")

        # low face existence check is always on the current window
        body_concent: float = self._body_concent_counter.get_concentration_ratio(
            WindowType.CURRENT, interval)
        self._grade_logger.info(f"body concentration = {body_concent}")
        # Directly take the body concentration as the final grade.
        interval.grade = body_concent
        self.s_concent_interval_refreshed.emit(interval)
        self._clear_windows(WindowType.CURRENT)

        review = "good" if interval.grade >= 0.6 else "bad"
        self._grade_logger.info(review + f" concentration: {interval.grade}")
        return True

    def _clear_windows(self, window_type: WindowType) -> None:
        """Clears the corresponding window of all grading components.

        Arguments:
            window_type: The type of window to be cleared.
        """
        self._body_concent_counter.clear_windows(window_type)
        self._interval_detector.clear_windows(window_type)
        if window_type is WindowType.CURRENT:
            self._face_existence_counter.clear_windows()
