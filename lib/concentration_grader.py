import logging
import time
from collections import deque
from typing import Deque, Optional, Tuple

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from nptyping import Int, NDArray

import lib.sliding_window as sliding_window
from fuzzy.grader import FuzzyGrader
from lib.blink_detector import AntiNoiseBlinkDetector, GoodBlinkRateIntervalDetector


logging.basicConfig(
    format="%(message)s",
    filename="concent_interval.log",
    level=logging.DEBUG,
)


class FaceExistenceRateCounter(sliding_window.SlidingWindowHandler):
    """Everytime a new frame is refreshed, there may exist a face or not. Count
    the existence within 1 minute and simply get the existence rate.
    """

    s_low_existence_detected = pyqtSignal(int)

    def __init__(self, low_existence: float = 0.66) -> None:
        super().__init__()
        self._low_existence = low_existence
        self._frame_times: Deque[int] = deque()
        self._face_times: Deque[int] = deque()

    @property
    def low_existence(self) -> float:
        return self._low_existence

    def add_frame(self) -> None:
        self._check_face_existence()
        current_time = int(time.time())
        self._frame_times.append(current_time)
        sliding_window.keep_sliding_window_in_one_minute(self._frame_times)
        # But also the face time needs to have the same window,
        # so we don't get the wrong value when get_face_existence_rate().
        sliding_window.keep_sliding_window_in_one_minute(self._face_times, current_time)

    def add_face(self) -> None:
        self._check_face_existence()
        time_stamp = int(time.time())
        self._face_times.append(time_stamp)
        sliding_window.keep_sliding_window_in_one_minute(self._face_times)
        # An add face should always be with an add frame,
        # so we don't need extra synchronization.

    def get_face_existence_rate(self) -> float:
        return round(len(self._face_times) / len(self._frame_times), 2)

    def clear_windows(self) -> None:
        self._frame_times.clear()
        self._face_times.clear()

    def _check_face_existence(self) -> None:
        """
        Emits:
            s_low_existence_detected
        """
        # Frame time is added every frame but face isn't,
        # so is used as the prerequisite for face existence check.
        if (self._frame_times
                and self._frame_times[-1] - self._frame_times[0] > 60
                and self.get_face_existence_rate() <= self._low_existence):
            self.s_low_existence_detected.emit(self._frame_times[0])


class ConcentrationGrader(sliding_window.SlidingWindowHandler):

    s_concent_interval_refreshed = pyqtSignal(int, float)  # start time, grade

    def __init__(
            self,
            ratio_threshold: float = 0.24,
            consec_frame: int = 3,
            # 0 is to trigger grade computation on no face interval, the user may be writing.
            good_rate_range: Tuple[int, int] = (0, 20),
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
                0 ~ 20 in default. For a proper blink rate, one may refer to
                https://pubmed.ncbi.nlm.nih.gov/11700965/#affiliation-1
                It's passed to the underlaying GoodBlinkRateIntervalDetector.
        """
        super().__init__()
        logging.info("ConcentrationGrader configs:")
        logging.info(f" ratio thres  = {ratio_threshold}")
        logging.info(f" consec frame = {consec_frame}")
        logging.info(f" good range   = {good_rate_range}\n")

        self._body_concentration_times: Deque[int] = deque()
        self._body_distraction_times: Deque[int] = deque()
        # TODO: Blink detection not accurate, lots of false blink.
        self._blink_detector = AntiNoiseBlinkDetector(ratio_threshold, consec_frame)
        self._interval_detector = GoodBlinkRateIntervalDetector(good_rate_range)
        self._face_existence_counter = FaceExistenceRateCounter(low_existence)
        self._fuzzy_grader = FuzzyGrader()

        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)
        self._interval_detector.s_good_interval_detected.connect(self.check_concentration)
        self._face_existence_counter.s_low_existence_detected.connect(self.check_concentration)
        # Clear the deque of frame, body and blink times only after the check_concentration() emits.
        # This is to make sure we don't miss any potential good concentration interval.
        self.s_concent_interval_refreshed.connect(self.clear_windows)

    def get_ratio_threshold_of_blink_detector(self) -> float:
        """Returns the ratio threshold used to consider an EAR lower than it
        to be a blink with noise."""
        return self._blink_detector.ratio_threshold

    def set_ratio_threshold_of_blink_detector(self, threshold: float) -> None:
        """
        Arguments:
            threshold:
                An eye aspect ratio lower than this is considered to be a blink with noise.
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
        self._body_concentration_times.append(int(time.time()))
        sliding_window.keep_sliding_window_in_one_minute(self._body_concentration_times)

    def add_body_distraction(self) -> None:
        self._body_distraction_times.append(int(time.time()))
        sliding_window.keep_sliding_window_in_one_minute(self._body_distraction_times)

    def get_body_concentration_grade(self, start_time: int) -> float:
        """Returns the amount of body concentration over total count.

        The result is rounded to two decimal places.
        """
        end_time: int = start_time + 60
        def count_time_in_interval(times: Deque[int]) -> int:
            # Iterate through the entire deque causes more time;
            # count all then remove out-of-ranges to provide slightly better efficiency.
            count: int = len(times)
            for t in times:
                if t > start_time:
                    break
                count -= 1
            for t in reversed(times):
                if t < end_time:
                    break
                count -= 1
            return count

        concent_count: int = count_time_in_interval(self._body_concentration_times)
        distract_count: int = count_time_in_interval(self._body_distraction_times)

        return round(concent_count / (concent_count + distract_count), 2)

    @pyqtSlot(int)
    @pyqtSlot(int, int)
    def check_concentration(
            self,
            start_time: int,
            blink_rate: Optional[int] = None) -> None:
        end_time: int = start_time + 60
        logging.info(f"check at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
        body_concent: float = self.get_body_concentration_grade(start_time)
        logging.info(f"body concentration = {body_concent}")

        grade: float
        if blink_rate is None:
            logging.info("low face existence, check body only:")
            grade = body_concent
        else:
            logging.info(f"blink rate = {blink_rate}")
            grade = self._fuzzy_grader.compute_grade(blink_rate, body_concent)

        if grade >= 0.6:
            self.s_concent_interval_refreshed.emit(start_time, grade)
            self.clear_windows()
            logging.info(f"good concentration: {grade}")
        else:
            logging.info(f"{grade}, not concentrating")
        logging.info("")  # separation

    @pyqtSlot()
    def clear_windows(self) -> None:
        self._body_distraction_times.clear()
        self._body_concentration_times.clear()
        self._interval_detector.clear_windows()
        self._face_existence_counter.clear_windows()


def to_date_time(epoch_time: int) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))
