import functools
import logging
from queue import PriorityQueue
from typing import Tuple

from PyQt5.QtCore import QObject, QThread, pyqtSignal
from nptyping import Int, NDArray

import concentration.fuzzy.parse as parse
import util.logger as logger
from blink.detector import AntiNoiseBlinkDetector
from concentration.criterion import (
    BlinkRateIntervalDetector,
    BodyConcentrationCounter,
    FaceExistenceRateCounter
)
from concentration.interval import IntervalType
from concentration.fuzzy.classes import Grade, Interval
from concentration.fuzzy.grader import FuzzyGrader
from util.path import to_abs_path
from util.sliding_window import WindowType
from util.task_worker import TaskWorker
from util.time import to_date_time


interval_logger: logging.Logger = logger.setup_logger(
    "interval_logger", to_abs_path("concent_interval.log"), logging.DEBUG)

class ConcentrationGrader(QObject):

    s_concent_interval_refreshed = pyqtSignal(int, int, float)  # start, end, grade

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
        interval_logger.info("ConcentrationGrader configs:")
        interval_logger.info(f" ratio thres  = {ratio_threshold}")
        interval_logger.info(f" consec frame = {consec_frame}")
        interval_logger.info(f" good range   = {good_rate_range}\n")

        self._interval_detector = BlinkRateIntervalDetector(good_rate_range)
        self._interval_detector.s_interval_detected.connect(self.put_interval_to_grade_in_queue)

        # TODO: Blink detection not accurate, lots of false blink.
        self._blink_detector = AntiNoiseBlinkDetector(ratio_threshold, consec_frame)
        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)

        self._face_existence_counter = FaceExistenceRateCounter(low_existence)
        self._face_existence_counter.s_low_existence_detected.connect(
            functools.partial(self.put_interval_to_grade_in_queue, IntervalType.LOW_FACE))

        self._body_concent_counter = BodyConcentrationCounter()
        self._fuzzy_grader = FuzzyGrader()

        self._json_file: str = to_abs_path("intervals.json")
        parse.init_json(self._json_file)

        # A queue that stores the intervals to grade.
        # The elements has the form:
        #   start and end of interval, type of interval, other information
        self._queue: PriorityQueue = PriorityQueue()
        # record the progress of grading time so we don't grade twice
        self._last_end_time: int = 0
        self._start_grading_thread()

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
        self._body_concent_counter.add_concentration()

    def add_body_distraction(self) -> None:
        self._body_concent_counter.add_distraction()

    def put_interval_to_grade_in_queue(
            self,
            type: IntervalType,
            start_time: int,
            end_time: int,
            *args) -> None:
        """
        The one that starts first should be graded first, if the time are the
        same, type with higher priority is graded first.
        """
        self._queue.put(((start_time, end_time), type, *args))

    def _start_grading_thread(self) -> None:
        """Starts the grading process in an individual thread."""
        self._worker = TaskWorker(self._grade_intervals)
        self._thread = QThread()
        self._worker.moveToThread(self._thread)
        # Worker starts running after the thread is started.
        self._thread.started.connect(self._worker.run)
        # TODO: Provide signal to tell that the grading app. is over.
        # connect(self._thread.quit)
        # connect(self._worker.deleteLater)
        # self._thread.finished.connect(self._thread.deleteLater)

        self._thread.start()

    def _grade_intervals(self) -> None:
        """An infinite loop that dispatches the intervals to their
        corresponding grading method.
        """
        while True:
            interval, type, *args = self._queue.get()
            if not self._is_graded_interval(interval):
                if type is IntervalType.LOW_FACE:
                    self._do_low_face_grading(*interval)
                else:
                    self._do_normal_grading(type, *interval, *args)
            self._queue.task_done()

    def _is_graded_interval(self, interval: Tuple[int, int]) -> bool:
        """Returns whether the interval starts before the last end time.

        Arguments:
            interval: The start and end time of such interval.
        """
        return interval[0] < self._last_end_time

    def _do_normal_grading(
            self,
            type: IntervalType,
            start_time: int,
            end_time: int,
            blink_rate: int) -> None:
        """Performs grading on real time and look back intervals."""
        interval_logger.info("in check at normal")

        interval_logger.info(f"Check at {to_date_time(start_time)} ~ "
                             f"{to_date_time(end_time)}")
        interval_logger.info(f"blink rate = {blink_rate}")

        window_type = WindowType.CURRENT
        if type is IntervalType.LOOK_BACK:
            window_type = WindowType.PREVIOUS
        body_concent: float = self._body_concent_counter.get_concentration_ratio(
            window_type, start_time, end_time)

        interval_logger.info(f"body concentration = {body_concent}")

        grade: float = self._fuzzy_grader.compute_grade(blink_rate, body_concent)
        if type is IntervalType.LOOK_BACK:
            grade = self._fuzzy_grader.compute_grade(
                # argument 1 of compute_grade has type int
                # TODO: An average-based blink rate might be floating-point number
                int((blink_rate * 60) / (end_time - start_time)), body_concent)
            self._last_end_time = end_time
            # A grading from the previous can only be bad, since they didn't
            # pass when they were current.
            self.s_concent_interval_refreshed.emit(start_time, end_time, grade)
            parse.append_to_json(
                self._json_file,
                Interval(start=start_time, end=end_time, grade=grade).__dict__)
            self._clear_windows(WindowType.PREVIOUS)
            interval_logger.info(f"bad concentration: {grade}")
        elif grade >= 0.6:
            self._last_end_time = end_time
            self.s_concent_interval_refreshed.emit(start_time, end_time, grade)
            parse.append_to_json(
                self._json_file,
                Interval(start=start_time, end=end_time, grade=grade).__dict__)
            # The grading of previous should precede current, not graded only if
            # the previous window isn't wide enough. So after the grading of current,
            # we should and must clear previous also.
            self._clear_windows(WindowType.PREVIOUS, WindowType.CURRENT)
            interval_logger.info(f"good concentration: {grade}")
        else:
            interval_logger.info(f"{grade}, not concentrating")
        interval_logger.info(f"leave check of normal {to_date_time(start_time)} ~ "
                             f"{to_date_time(end_time)}")
        interval_logger.info("")  # separation

    def _do_low_face_grading(self, start_time: int, end_time: int) -> None:
        """
        Note that no matter good or bad, the low face interval is always graded
        currently.
        """
        interval_logger.info("in check at low face")

        interval_logger.info(f"Check at {to_date_time(start_time)} ~ "
                             f"{to_date_time(end_time)}")
        interval_logger.info("low face existence, check body only:")

        # low face existence check is always on the current window
        body_concent: float = self._body_concent_counter.get_concentration_ratio(
            WindowType.CURRENT, start_time, end_time)
        grade: float = body_concent
        self._last_end_time = end_time
        self.s_concent_interval_refreshed.emit(start_time, end_time, grade)
        parse.append_to_json(
            self._json_file,
            Interval(start=start_time, end=end_time, grade=grade).__dict__
        )
        self._clear_windows(WindowType.CURRENT)

        interval_logger.info(f"concentration: {grade}")
        interval_logger.info(f"leave check of low face {to_date_time(start_time)} ~ "
                             f"{to_date_time(end_time)}")
        interval_logger.info("")  # separation

    def _clear_windows(self, *args: WindowType) -> None:
        """Clears the corresponding window of all grading components.

        Arguments:
            args: Various amount of window types.
        """
        self._body_concent_counter.clear_windows(*args)
        self._interval_detector.clear_windows(*args)

        if WindowType.CURRENT in args:
            self._face_existence_counter.clear_windows()
