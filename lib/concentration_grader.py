import functools
import json
import logging
import math
import time
from typing import Deque, List, Optional, Tuple, Union

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from nptyping import Int, NDArray

import fuzzy.parse as parse
import util.logger as logger
from fuzzy.classes import Grade, Interval
from fuzzy.grader import FuzzyGrader
from lib.blink_detector import (AntiNoiseBlinkDetector, BlinkRateIntervalDetector,
                                GoodBlinkRateIntervalDetector, IntervalLevel)
from lib.path import to_abs_path
from lib.sliding_window import DoubleTimeWindow, TimeWindow


interval_logger: logging.Logger = logger.setup_logger("interval_logger",
                                                      to_abs_path("..\concent_interval.log"),
                                                      logging.DEBUG)

class FaceExistenceRateCounter(QObject):
    """Everytime a new frame is refreshed, there may exist a face or not. Count
    the existence within 1 minute and simply get the existence rate.

    Signals:
        s_low_existence_detected:
            Emits when face existence is low and sends the face existence ratio.
    """

    s_low_existence_detected = pyqtSignal(int)

    def __init__(self, low_existence: float = 0.66) -> None:
        """
        Arguments:
            low_existence:
                Ratio of face over frame lower then this indicates a low face
                existence. 0.66 (2/3) in default.
        """
        super().__init__()
        self._low_existence = low_existence
        self._frame_times = TimeWindow(60)
        self._frame_times.set_time_catch_callback(self._check_face_existence)
        self._face_times = TimeWindow(60)
        self._face_times.set_time_catch_callback(self._check_face_existence)

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
        # so we don't get the wrong value when get_face_existence_rate().
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

    def get_face_existence_rate(self) -> float:
        """Returns the face existence rate of the minute.

        The rate is rounded to two decimal places.
        """
        return round(len(self._face_times) / len(self._frame_times), 2)

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
                Emits when face existence is low and sends the face existence rate.
        """
        # Frame time is added every frame but face isn't,
        # so is used as the prerequisite for face existence check.
        if (self._frame_times
                and self._frame_times[-1] - self._frame_times[0] > 60
                and self.get_face_existence_rate() <= self._low_existence):
            self.s_low_existence_detected.emit(self._frame_times[0])


class ConcentrationGrader(QObject):

    s_concent_interval_refreshed = pyqtSignal(IntervalLevel, int, int, float)  # start, end, grade

    def __init__(
            self,
            ratio_threshold: float = 0.24,
            consec_frame: int = 3,
            # 0 is to trigger grade computation on no face interval, the user may be writing.
            good_rate_range: Tuple[int, int] = (0, 21),
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
                0 ~ 21 in default. For a proper blink rate, one may refer to
                https://pubmed.ncbi.nlm.nih.gov/11700965/#affiliation-1
                It's passed to the underlaying GoodBlinkRateIntervalDetector.
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
        # self._face_existence_counter = FaceExistenceRateCounter(low_existence)
        self._fuzzy_grader = FuzzyGrader()

        self._json_file: str = to_abs_path("..\good_intervals.json")
        parse.init_json(self._json_file)

        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)
        self._interval_detector.s_good_interval_detected.connect(
            functools.partial(self.check_concentration, IntervalLevel.GOOD))
        self._interval_detector.s_bad_interval_detected.connect(
            functools.partial(self.check_concentration, IntervalLevel.BAD))
        # self._face_existence_counter.s_low_existence_detected.connect(self.check_concentration)
        # Clear the window of frame, body and blink times only after the
        # check_concentration() emits.
        # This is to make sure we don't miss any potential good concentration interval.
        self.s_concent_interval_refreshed.connect(self.clear_windows)

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
        # self._face_existence_counter.add_frame()
        # Basicly, add_frame() is called every frame,
        # so call method which should be called manually together.
        self._interval_detector.check_blink_rate()

    def add_face(self) -> None:
        # self._face_existence_counter.add_face()
        pass

    def add_body_concentration(self) -> None:
        self._body_concentration_times.append_time()

    def add_body_distraction(self) -> None:
        self._body_distraction_times.append_time()

    def get_body_concentration_grade(
            self,
            level: IntervalLevel,
            start_time: int,
            end_time: int) -> float:
        """Returns the amount of body concentration over total count.

        The result is rounded to two decimal places.
        """
        def count_time_in_interval(times: DoubleTimeWindow) -> int:
            window: Union[DoubleTimeWindow, Deque[int]] = times
            if level is IntervalLevel.BAD:
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
        # FIXME: ZeroDivisionError occurs after an undesired double check of a same interval
        # Maybe there's a time before windows are cleared but after the first check.
        return round(concent_count / (concent_count + distract_count), 2)

    @pyqtSlot(int, int)
    @pyqtSlot(int, int, int)
    def check_concentration(
            self,
            level: IntervalLevel,
            start_time: int,
            end_time: int,
            blink_rate: Optional[int] = None) -> None:
        interval_logger.info(f"check at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
        body_concent: float = self.get_body_concentration_grade(level, start_time, end_time)
        interval_logger.info(f"body concentration = {body_concent}")

        grade: float
        if blink_rate is None:
            interval_logger.info("low face existence, check body only:")
            grade = body_concent
        else:
            interval_logger.info(f"blink rate = {blink_rate}")
            grade = self._fuzzy_grader.compute_grade(blink_rate, body_concent)

        if level is IntervalLevel.BAD:
            self.s_concent_interval_refreshed.emit(level, start_time, end_time, grade)
            interval_logger.info(f"bad concentration: {grade}")
            parse.append_to_json(
                self._json_file,
                Interval(start=start_time, end=end_time, grade=grade).__dict__
            )
        elif grade >= 0.6:
            self.s_concent_interval_refreshed.emit(level, start_time, end_time, grade)
            interval_logger.info(f"good concentration: {grade}")
            parse.append_to_json(
                self._json_file,
                Interval(start=start_time, end=end_time, grade=grade).__dict__
            )
        else:
            interval_logger.info(f"{grade}, not concentrating")
        interval_logger.info("")  # separation

    @pyqtSlot(IntervalLevel)
    def clear_windows(self, level: IntervalLevel) -> None:
        prev_only: bool = False
        if level is IntervalLevel.BAD:
            prev_only = True
        self._body_distraction_times.clear(prev_only=prev_only)
        self._body_concentration_times.clear(prev_only=prev_only)
        self._interval_detector.clear_windows(level)
        # self._face_existence_counter.clear_windows()


def save_chart_of_intervals(filename: str, intervals: List[Interval]) -> None:
    if not intervals:
        raise ValueError("intervals can't be empty")

    start_times: List[float] = []
    interval_lengths: List[float] = []
    grades: List[float] = []

    init_time: int = intervals[0].start
    for interval in intervals:
        start_times.append((interval.start - init_time) / 60)
        interval_lengths.append((interval.end - interval.start) / 60)
        grades.append(interval.grade)

    fig, ax = plt.subplots(figsize=(12, 6))

    ax.bar(start_times, grades, width=interval_lengths, align="edge")
    ax.set_xticks(range(math.ceil(start_times[-1]) + 2))
    ax.set_yticks(np.arange(0, 1.2, 0.2))
    ax.set_yticks(np.arange(0.1, 1.0, 0.2), minor=True)
    ax.set_ylim(0, 1.1)
    ax.axhline(y=0.6, linestyle="dashed", color="black")
    ax.set_ylabel("grade")
    ax.set_xlabel("time (min)")
    ax.set_title(f"Concentration grades from {to_date_time(init_time)}")
    fig.savefig(filename)


def to_date_time(epoch_time: int) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))
