import logging
from typing import Tuple

from PyQt5.QtCore import QObject, pyqtSignal
from nptyping import Int, NDArray

import fuzzy.parse as parse
import util.logger as logger
from blink.detector import AntiNoiseBlinkDetector
from blink.interval import BlinkRateIntervalDetector, IntervalLevel
from counter import BodyConcentrationCounter, FaceExistenceRateCounter
from fuzzy.classes import Interval
from fuzzy.grader import FuzzyGrader
from util.path import to_abs_path
from util.sliding_window import WindowType
from util.time import to_date_time


interval_logger: logging.Logger = logger.setup_logger("interval_logger",
                                                      to_abs_path("concent_interval.log"),
                                                      logging.DEBUG)

class ConcentrationGrader(QObject):

    s_concent_interval_refreshed = pyqtSignal(IntervalLevel, int, int, float)  # start, end, grade

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
                The number of consecutive frames the eye must be below the threshold
                to indicate a blink. 3 in default.
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

        # TODO: Blink detection not accurate, lots of false blink.
        self._blink_detector = AntiNoiseBlinkDetector(ratio_threshold, consec_frame)
        self._interval_detector = BlinkRateIntervalDetector(good_rate_range)
        self._face_existence_counter = FaceExistenceRateCounter(low_existence)
        self._body_concent_counter = BodyConcentrationCounter()
        self._fuzzy_grader = FuzzyGrader()

        self._json_file: str = to_abs_path("intervals.json")
        parse.init_json(self._json_file)

        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)
        self._interval_detector.s_interval_detected.connect(self.check_normal_concentration)
        self._face_existence_counter.s_low_existence_detected.connect(self.check_low_face_concentration)

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

    def check_normal_concentration(
            self,
            type: WindowType,
            start_time: int,
            end_time: int,
            blink_rate: int) -> None:
        interval_logger.info("in check at normal")

        interval_logger.info(f"Check at {to_date_time(start_time)} ~ "
                             f"{to_date_time(end_time)}")
        interval_logger.info(f"blink rate = {blink_rate}")
        body_concent: float = self._body_concent_counter.get_concentration_ratio(
            type, start_time, end_time)
        interval_logger.info(f"body concentration = {body_concent}")

        grade: float = self._fuzzy_grader.compute_grade(blink_rate, body_concent)
        if type is WindowType.PREVIOUS:
            grade = self._fuzzy_grader.compute_grade(
                # argument 1 of compute_grade has type int
                # TODO: An average-based blink rate might be floating-point number
                int((blink_rate * 60) / (end_time - start_time)), body_concent)
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
        interval_logger.info(f"leave check of normal {to_date_time(start_time)} ~ "
                             f"{to_date_time(end_time)}")
        interval_logger.info("")  # separation

    def check_low_face_concentration(self, start_time: int, end_time: int) -> None:
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

        level = IntervalLevel.GOOD if grade >= 0.6 else IntervalLevel.BAD
        self.s_concent_interval_refreshed.emit(level, start_time, end_time, grade)
        parse.append_to_json(
            self._json_file,
            Interval(start=start_time, end=end_time, grade=grade).__dict__
        )
        self.clear_windows(WindowType.CURRENT)

        interval_logger.info(f"concentration: {grade}")
        interval_logger.info(f"leave check of low face {to_date_time(start_time)} ~ "
                             f"{to_date_time(end_time)}")
        interval_logger.info("")  # separation

    def clear_windows(self, *args: WindowType) -> None:
        """Clears the corresponding window of all grading components.

        Arguments:
            args: Various amount of window types.
        """
        self._body_concent_counter.clear_windows(*args)
        self._interval_detector.clear_windows(*args)

        if WindowType.CURRENT in args:
            self._face_existence_counter.clear_windows()
