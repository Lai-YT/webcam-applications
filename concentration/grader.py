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
from concentration.fuzzy.classes import Grade, Interval
from concentration.fuzzy.grader import FuzzyGrader
from concentration.interval import IntervalType
from util.heap import MinHeap
from util.logger import setup_logger
from util.path import to_abs_path
from util.sliding_window import WindowType
from util.time import ONE_MIN, get_current_time, to_date_time


class ConcentrationGrader(QObject):

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
        self._grade_logger: logging.Logger = setup_logger(
            "grade_logger", to_abs_path("grades.log"), logging.DEBUG)
        self._grade_logger.info(f"Grader starts at {to_date_time(get_current_time())}\n")

        self._interval_detector = BlinkRateIntervalDetector(good_rate_range)
        self._interval_detector.s_interval_detected.connect(self.push_interval_to_grade_in_heap)
        self._interval_timer = QTimer(self)
        self._interval_timer.timeout.connect(self._interval_detector.check_blink_rate)
        self._interval_timer.start(1_000)  # 1s

        # FIXME: Blink detection not accurate, lots of false blink.
        self._blink_detector = AntiNoiseBlinkDetector(ratio_threshold, consec_frame)
        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)

        self._body_concent_counter = BodyConcentrationCounter()
        self._fuzzy_grader = FuzzyGrader()

        self._json_file: str = to_abs_path("intervals.json")
        parse.init_json(self._json_file)
        self.s_concent_interval_refreshed.connect(
            lambda interval: parse.append_to_json(self._json_file, interval.__dict__))

        # Min heaps that store the intervals to grade.
        # The elements has the form:
        #   Interval(start and end time), type of interval, other information
        #
        # The curr heap has the REAL_TIME and LOW_FACEs, which are in the current
        # windows; the prev heap has the LOOK_BACKs, which are in the previous.
        self._curr_heap = MinHeap()
        self._look_backs = MinHeap()

        # record the progress of grading time so we don't grade twice
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

    def add_body_concentration(self) -> None:
        self._body_concent_counter.add_concentration()

    def add_body_distraction(self) -> None:
        self._body_concent_counter.add_distraction()

    @pyqtSlot(Interval, IntervalType)
    @pyqtSlot(Interval, IntervalType, int)
    def push_interval_to_grade_in_heap(
            self,
            interval: Interval,
            type: IntervalType,
            blink_rate: Optional[int] = None) -> None:
        """
        The one that starts first should be graded first. If the time are the
        same, type with higher priority is graded first.
        """
        if type is IntervalType.LOOK_BACK:
            heap = self._look_backs
        else:
            heap = self._curr_heap
        heap.push((interval, type, blink_rate))

    def _grade_intervals(self) -> None:
        """Dispatches the intervals to their corresponding grading method."""
        record: bool
        # First, grade the LOOK_BACKs.
        while self._look_backs:
            interval, type, blink_rate = self._look_backs.pop()
            if not self._is_graded_interval(interval):
                record = self._perform_grading(interval, type, blink_rate)
                if record:
                    self._last_end_time = interval.end
                    self._interval_detector.sync_last_end_up(self._last_end_time)
        # Second, grade the REAL_TIMEs. Additionally grade EXTRUSIONs if existed.
        while self._curr_heap:
            interval, type, blink_rate = self._curr_heap.pop()
            if not self._is_graded_interval(interval):
                if type is IntervalType.LOW_FACE:
                    # LOW_FACEs aren't under consideration yet.
                    pass
                if type is IntervalType.REAL_TIME:
                    record = self._perform_grading(interval, type, blink_rate)
                    if record:
                        extrude_interval: Optional[Tuple[Interval, IntervalType, int]] = (
                            self._interval_detector.get_extrude_interval())
                        if (extrude_interval is not None
                                and not self._is_graded_interval(extrude_interval[0])):
                            self._perform_grading(*extrude_interval)
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

    def _perform_grading(
            self,
            interval: Interval,
            type: IntervalType,
            blink_rate: int) -> bool:
        """Performs grading on real time and look back intervals and records it
        if the grade is high enough.

        Arguments:
            interval: The interval dataclass which contains start and end time.
            type: The type of such interval.
            blink_rate: The blink rate in that interval.

        Returns:
            True if the grading result is record, otherwise False.

        Emits:
            s_concent_interval_refreshed:
                Emits if the the grading result is record and sends the grade.
        """
        self._grade_logger.info(f"Normal check at {to_date_time(interval.start)} ~ "
                             f"{to_date_time(interval.end)}")
        self._grade_logger.info(f"blink rate = {blink_rate}")

        window_type = WindowType.CURRENT
        if type in {IntervalType.LOOK_BACK, IntervalType.EXTRUSION}:
            window_type = WindowType.PREVIOUS

        body_concent: float = self._body_concent_counter.get_concentration_ratio(
            window_type, interval)
        self._grade_logger.info(f"body concentration = {body_concent}")

        if type is IntervalType.LOOK_BACK:
            interval.grade = self._fuzzy_grader.compute_grade(blink_rate, body_concent)
            self.s_concent_interval_refreshed.emit(interval)
            self._clear_windows(window_type)
            # A grading on look back can only be bad, since they didn't
            # pass when they were real time.
            self._grade_logger.info(f"bad concentration: {interval.grade}")
            return True
        elif type is IntervalType.EXTRUSION:
            interval.grade = self._fuzzy_grader.compute_grade(
                # FIXME: An average-based blink rate might be floating-point number
                # But argument 1 of compute_grade has type int.
                int((blink_rate*ONE_MIN) / (interval.end-interval.start)), body_concent)
            self.s_concent_interval_refreshed.emit(interval)
            self._clear_windows(window_type)
            # A grading on look back can only be bad, since they didn't
            # pass when they were real time.
            self._grade_logger.info(f"bad concentration: {interval.grade}")
            return True

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

    def _clear_windows(self, window_type: WindowType) -> None:
        """Clears the corresponding window of all grading components.

        Arguments:
            window_type: The type of window to be cleared.
        """
        self._body_concent_counter.clear_windows(window_type)
        self._interval_detector.clear_windows(window_type)
