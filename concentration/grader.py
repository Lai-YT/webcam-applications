import functools
import time
import logging
from typing import Tuple

from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from nptyping import Int, NDArray

import concentration.fuzzy.parse as parse
import util.logger as logger
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
from util.path import to_abs_path
from util.sliding_window import WindowType
from util.time import get_current_time, to_date_time


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
        self._interval_logger: logging.Logger = logger.setup_logger(
            "interval_logger", to_abs_path("concent_interval.log"), logging.DEBUG)
        self._interval_logger.info(f"Grader starts at {to_date_time(get_current_time())}\n")

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

        # A min heap that stores the intervals to grade.
        # The elements has the form:
        #   Interval(start and end time), type of interval, other information
        self._heap = MinHeap()
        # record the progress of grading time so we don't grade twice
        self._last_end_time: int = 0

        self._process_timer = QTimer(self)
        self._process_timer.timeout.connect(self._grade_intervals)
        self._process_timer.start(1_000)

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

    def add_body_concentration(self) -> None:
        self._body_concent_counter.add_concentration()

    def add_body_distraction(self) -> None:
        self._body_concent_counter.add_distraction()

    def push_interval_to_grade_in_heap(
            self,
            interval: Interval,
            type: IntervalType,
            *args) -> None:
        """
        The one that starts first should be graded first. If the time are the
        same, type with higher priority is graded first.
        """
        self._heap.push((interval, type, *args))

    def _grade_intervals(self) -> None:
        """An infinite loop that dispatches the intervals to their
        corresponding grading method.
        """
        # grade all those can be grade
        while self._heap:
            interval, type, *args = self._heap.pop()
            if not self._is_graded_interval(interval):
                if type is IntervalType.LOW_FACE:
                    self._do_low_face_grading(interval)
                elif type is IntervalType.REAL_TIME:
                    self._do_normal_grading(interval, type, *args)
                elif type is IntervalType.LOOK_BACK:
                    # A look back interval within 60 seconds is followed by a
                    # "likely" good interval. We grade the look back only if the
                    # following interval is a "truly" good interval.
                    if interval.end - interval.start < 60:
                        # Grade the following real time or low face interval first.
                        fol_int, fol_type, *fol_args = self._heap.pop()
                        while fol_type is IntervalType.LOOK_BACK:
                            fol_int, fol_type, *fol_args = self._heap.pop()
                        self._do_normal_grading(fol_int, fol_type, *fol_args)
                        # The last end is updated, which mean it's a "truly"
                        # good interval, so we can now look back.
                        if self._last_end_time >= interval.end:
                            self._do_normal_grading(interval, type, *args)
                    else:
                        self._do_normal_grading(interval, type, *args)

    def _is_graded_interval(self, interval: Interval) -> bool:
        """Returns whether the interval starts before the last end time.

        Arguments:
            interval: The interval dataclass which contains start and end time.
        """
        return interval.start < self._last_end_time

    def _do_normal_grading(
            self,
            interval: Interval,
            type: IntervalType,
            blink_rate: int) -> None:
        """Performs grading on real time and look back intervals."""
        self._interval_logger.info(f"Normal check at {to_date_time(interval.start)} ~ "
                             f"{to_date_time(interval.end)}")
        self._interval_logger.info(f"blink rate = {blink_rate}")

        window_type = WindowType.CURRENT
        if type is IntervalType.LOOK_BACK:
            window_type = WindowType.PREVIOUS

        body_concent: float = self._body_concent_counter.get_concentration_ratio(
            window_type, interval)
        self._interval_logger.info(f"body concentration = {body_concent}")

        if type is IntervalType.LOOK_BACK:
            interval.grade = self._fuzzy_grader.compute_grade(
                # FIXME: An average-based blink rate might be floating-point number
                # But argument 1 of compute_grade has type int.
                int((blink_rate*60) / (interval.end-interval.start)), body_concent)
            # A look back can go after real time, but we should backward the time.
            self._last_end_time = max(interval.end, self._last_end_time)
            self._interval_detector.sync_last_end_up(self._last_end_time)

            self.s_concent_interval_refreshed.emit(interval)
            parse.append_to_json(self._json_file, interval.__dict__)
            self._clear_windows(WindowType.PREVIOUS)
            # A grading on look back can only be bad, since they didn't
            # pass when they were real time.
            self._interval_logger.info(f"bad concentration: {interval.grade}")
        else:
            grade: float = self._fuzzy_grader.compute_grade(blink_rate, body_concent)
            if grade >= 0.6:
                self._last_end_time = interval.end
                self._interval_detector.sync_last_end_up(self._last_end_time)
                interval.grade = grade
                self.s_concent_interval_refreshed.emit(interval)
                parse.append_to_json(self._json_file, interval.__dict__)
                self._clear_windows(WindowType.CURRENT)
                self._interval_logger.info(f"good concentration: {interval.grade}")
            else:
                self._interval_logger.info(f"{grade}, not concentrating")
        self._interval_logger.info(f"leave check of normal {to_date_time(interval.start)} ~ "
                             f"{to_date_time(interval.end)}")
        self._interval_logger.info("")  # separation

    def _clear_windows(self, window_type: WindowType) -> None:
        """Clears the corresponding window of all grading components.

        Arguments:
            window_type: The type of window to be cleared.
        """
        self._body_concent_counter.clear_windows(window_type)
        self._interval_detector.clear_windows(window_type)
