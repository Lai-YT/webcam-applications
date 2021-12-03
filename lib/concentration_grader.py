import logging
import time
from collections import deque
from typing import Deque, Optional, Tuple

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from nptyping import Int, NDArray

import lib.fuzzy as fuzzy
from lib.blink_detector import AntiNoiseBlinkDetector, GoodBlinkRateIntervalDetector


logging.basicConfig(
    format="%(message)s",
    filename="concent_interval.log",
    level=logging.DEBUG,
)


class FaceExistenceRateCounter(QObject):
    """Everytime a new frame is refreshed, there may exist a face or not. Count
    the existence within 1 minute and simply get the existence rate.
    """

    s_low_existence_detected = pyqtSignal(int, int)

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
        time_stamp = int(time.time())
        self._frame_times.append(time_stamp)
        keep_sliding_window_in_one_minute(self._frame_times)
        # But also the face time needs to be synced up,
        # so we don't get the wrong value when get_face_existence_rate().
        while self._face_times and time_stamp - self._face_times[0] > 60:
            self._face_times.popleft()

    def add_face(self) -> None:
        self._check_face_existence()
        time_stamp = int(time.time())
        self._face_times.append(time_stamp)
        keep_sliding_window_in_one_minute(self._face_times)
        # An add face should always be with an add frame,
        # so we don't need extra synchronization.

    def get_face_existence_rate(self) -> float:
        return round(len(self._face_times) / len(self._frame_times), 2)

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
            self.s_low_existence_detected.emit(self._frame_times[0], self._frame_times[-1])
            self._frame_times.clear()
            self._face_times.clear()

# FIXME: Broken when low face existence: ZeroDivisionError occurs in get_body_concentration_grade.
class ConcentrationGrader(QObject):

    s_concent_interval_refreshed = pyqtSignal(int, int, float)  # start time, end time, grade

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
        # TODO: BLink detection not accurate, lots of false blink.
        self._blink_detector = AntiNoiseBlinkDetector(ratio_threshold, consec_frame)
        self._interval_detector = GoodBlinkRateIntervalDetector(good_rate_range)
        self._face_existence_counter = FaceExistenceRateCounter(low_existence)

        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)
        self._interval_detector.s_good_interval_detected.connect(self.check_concentration)
        self._face_existence_counter.s_low_existence_detected.connect(self.check_concentration)

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

    def add_face(self) -> None:
        self._face_existence_counter.add_face()

    def add_body_concentration(self) -> None:
        self._body_concentration_times.append(int(time.time()))
        keep_sliding_window_in_one_minute(self._body_concentration_times)

    def add_body_distraction(self) -> None:
        self._body_distraction_times.append(int(time.time()))
        keep_sliding_window_in_one_minute(self._body_distraction_times)

    def get_body_concentration_grade(self, start_time: int, end_time: int) -> float:
        """Returns the amount of body concentration over total count.

        The result is rounded to two decimal places.
        """
        # Iterate through the entire deque causes more time;
        # count all then remove out-of-ranges to provide slightly better efficiency.
        concent_count: int = len(self._body_concentration_times)
        for concent_time in self._body_concentration_times:
            if concent_time > start_time:
                break
            concent_count -= 1
        for concent_time in reversed(self._body_concentration_times):
            if concent_time < end_time:
                break
            concent_count -= 1

        distract_count: int = len(self._body_distraction_times)
        for distract_time in self._body_distraction_times:
            if distract_time > start_time:
                break
            distract_count -= 1
        for distract_time in reversed(self._body_distraction_times):
            if distract_time < end_time:
                break
            distract_count -= 1

        return round(concent_count / (concent_count + distract_count), 2)

    @pyqtSlot(int, int)
    @pyqtSlot(int, int, int)
    def check_concentration(
            self,
            start_time: int,
            end_time: int,
            blink_rate: Optional[int] = None) -> None:
        logging.info(f"check at {to_date_time(start_time)} ~ {to_date_time(end_time)}, {blink_rate}")
        body_concent: float = self.get_body_concentration_grade(start_time, end_time)
        logging.info(f"body concentration = {body_concent}")

        grade: float
        if blink_rate is None:
            logging.info("low face existence, check body only:")
            grade = body_concent
        else:
            logging.info(f"blink rate = {blink_rate}")
            grade = fuzzy.compute_grade(blink_rate, body_concent)

        if grade >= 0.6:
            self.s_concent_interval_refreshed.emit(start_time, end_time, grade)
            logging.info(f"good concentration: {grade}")
        else:
            logging.info(f"{grade}, not concentrating")
        logging.info("")  # separation


def keep_sliding_window_in_one_minute(window: Deque[int]) -> None:
    """Compares the earliest and latest time stamp in the window, keep them within a minute.

    Arguments:
        window: The time stamps. Should be sorted in ascending order with respect to time.
    """
    while window and window[-1] - window[0] > 60:
        window.popleft()


def to_date_time(epoch_time: int) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))
