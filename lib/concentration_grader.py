import logging
import time
from collections import deque
from typing import Deque

from PyQt5.QtCore import QObject, pyqtSignal

import lib.blink_detector as bd


logging.basicConfig(
	format="%(asctime)s %(message)s",
	datefmt="%I:%M:%S",
	filename="concent_interval.log",
	level=logging.DEBUG,
)


class ConcentrationGrader(QObject):

    s_concent_interval_refreshed = pyqtSignal(int, int)  # start time, end time

    def __init__(self, blink_detector: bd.AntiNoiseBlinkDetector) -> None:
        super().__init__()

        self._body_concentrations: Deque[int] = deque()
        self._body_distractions: Deque[int] = deque()

        self._blink_detector = blink_detector
        self._interval_detector = bd.GoodBlinkRateIntervalDetector((15, 25))
        self._blink_detector.s_blinked.connect(self._interval_detector.add_blink)
        self._interval_detector.s_good_interval_detected.connect(self.check_body_concentration)
        self._interval_detector.s_good_interval_detected.connect(
            lambda start, end: logging.info(f"good blink rate at {start} ~ {end}"))
        self.s_concent_interval_refreshed.connect(
            lambda start, end: logging.info(f"good concentration at {start} ~ {end}"))

    @property
    def blink_detector(self) -> bd.AntiNoiseBlinkDetector:
		"""Returns the AntiNoiseBlinkDetector used by the ConcentrationGrader."""
        return self._blink_detector

    def add_body_concentration(self) -> None:
        self._body_concentrations.append(int(time.time()))
        while (self._body_concentrations
                and (self._body_concentrations[-1] - self._body_concentrations[0]) > 60):
            self._body_concentrations.popleft()

    def add_body_distraction(self) -> None:
        self._body_distractions.append(int(time.time()))
        while (self._body_distractions
                and (self._body_distractions[-1] - self._body_distractions[0]) > 60):
            self._body_distractions.popleft()

    def check_body_concentration(self, start_time: int, end_time: int) -> None:
        # get concentration
        concent_count: int = 0
        for concent_time in self._body_concentrations:
            if concent_time < start_time or concent_time > end_time:
                break
            concent_count += 1

        # get concentration
        distract_count: int = 0
        for distract_time in self._body_distractions:
            if distract_time < start_time or distract_time > end_time:
                break
            distract_count += 1

        logging.info(f"body concentration is {concent_count / (concent_count + distract_count):.2f}")
        # more than 66%
        if concent_count > distract_count*2:
            self.s_concent_interval_refreshed.emit(start_time, end_time)
