import logging
import time
from collections import deque
from typing import Deque, Tuple

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot
from nptyping import Int, NDArray

from lib.blink_detector import AntiNoiseBlinkDetector, GoodBlinkRateIntervalDetector


logging.basicConfig(
    format="%(message)s",
    filename="concent_interval.log",
    level=logging.DEBUG,
)


class FaceExistenceRateCounter:
    """Everytime a new frame is refreshed, there may exist a face or not. Count
    the existence within 1 minute and simply get the existence rate.
    """
    def __init__(self) -> None:
        self._frame_times: Deque[int] = deque()
        self._face_times: Deque[int] = deque()

    def add_frame(self) -> None:
        self._frame_times.append(int(time.time()))
        keep_sliding_window_in_one_minute(self._frame_times)

    def add_face(self) -> None:
        self._face_times.append(int(time.time()))
        keep_sliding_window_in_one_minute(self._face_times)

    def get_face_existence_rate(self) -> float:
        return round(len(self._face_times) / len(self._frame_times), 2)


class ConcentrationGrader(QObject):

    s_concent_interval_refreshed = pyqtSignal(int, int)  # start time, end time

    def __init__(
            self,
            ratio_threshold: float = 0.24,
            consec_frame: int = 3,
            good_rate_range: Tuple[int, int] = (10, 30)) -> None:
        super().__init__()
        logging.info("ConcentrationGrader configs:")
        logging.info(f" ratio thres  = {ratio_threshold}")
        logging.info(f" consec frame = {consec_frame}")
        logging.info(f" good range   = {good_rate_range}\n")

        self._body_concentration_times: Deque[int] = deque()
        self._body_distraction_times: Deque[int] = deque()

        self._blink_detector = AntiNoiseBlinkDetector(ratio_threshold, consec_frame)
        self._interval_detector = GoodBlinkRateIntervalDetector(good_rate_range)
        self._face_existence_counter = FaceExistenceRateCounter()

        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)
        self._interval_detector.s_good_interval_detected.connect(self.check_body_concentration)

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

    @pyqtSlot(int, int, int)
    def check_body_concentration(self, start_time: int, end_time: int, blink_rate: int) -> None:
        logging.info(f"good blink rate at {to_date_time(start_time)} ~ {to_date_time(end_time)}, rate = {blink_rate}")
        face_existence_rate: float = self._face_existence_counter.get_face_existence_rate()
        if face_existence_rate < 0.6:
            logging.info("low face existence, not reliable")

        # get concentration
        concent_count: int = 0
        for concent_time in self._body_concentration_times:
            if concent_time < start_time or concent_time > end_time:
                break
            concent_count += 1

        # get concentration
        distract_count: int = 0
        for distract_time in self._body_distraction_times:
            if distract_time < start_time or distract_time > end_time:
                break
            distract_count += 1

        logging.info(f"body concentration is {concent_count / (concent_count + distract_count):.2f}")
        # more than 66%
        if concent_count > distract_count*2:
            self.s_concent_interval_refreshed.emit(start_time, end_time)
            logging.info(f"good concentration at {to_date_time(start_time)} ~ {to_date_time(end_time)}")
        logging.info("")


def keep_sliding_window_in_one_minute(window: Deque[int]) -> None:
    """Compares the earliest and latest time stamp in the window, keep them within a minute.

    Arguments:
        window: The time stamps. Should be sorted in ascending order with respect to time.
    """
    while window and window[-1] - window[0] > 60:
        window.popleft()


def to_date_time(epoch_time: int) -> str:
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(epoch_time))
