# reference:
# https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/

import math
import time
import statistics
from enum import Enum, auto
from typing import List, Optional, Tuple

import cv2
from PyQt5.QtCore import QObject, pyqtSignal
from imutils import face_utils
from nptyping import Int, NDArray

from lib.color import BGR, GREEN
from lib.image_type import ColorImage


class EyeSide(Enum):
    LEFT  = auto()
    RIGHT = auto()


class TailorMadeNormalEyeAspectRatioMaker:
    """Take a certain number of landmarks that contains face to determine
    a tailor-made normal EAR of the user.

    It can be used with a BlinkDetector to provide better detections on different
    users.
    """
    def __init__(
            self,
            temp_ratio: float = 0.3,
            number_threshold: int = 100) -> None:
        """
        Arguments:
            temp_ratio:
                Used before the normal EAR is determined. Prevents from getting
                an unreliable normal EAR due to low number of samples.
            number_threshold: Number of samples higher than this is considered to be reliable.
        """
        if temp_ratio < 0.15 or temp_ratio > 0.5:
            raise ValueError("normal eye aspect ratio should >= 0.15 and <= 0.5")
        if number_threshold < 100:
            raise ValueError("number of samples under 100 makes the normal eye aspect ratio susceptible to extreme values")

        self._temp_ratio = temp_ratio
        self._number_threshold = number_threshold
        # TODO: Any better data structure to queue, sort and sum?
        self._sample_ratios: List[float] = []

    def read_sample(self, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Reads in landmarks of face, gets its EAR value and stores as a sample.

        Arguments:
            landmarks: (x, y) coordinates of the 68 face landmarks.
        """
        # Empty landmarks is not count.
        if not landmarks.any():
            return
        self._sample_ratios.append(BlinkDetector.get_average_eye_aspect_ratio(landmarks))
        # Keep the length of the samples fixed to number threshold,
        # which is the most recent samples.
        if len(self._sample_ratios) > self._number_threshold:
            self._sample_ratios.pop(0)

    def get_normal_ratio(self) -> Tuple[int, float]:
        """Returns the tailor-made EAR when the number of sample ratios is
        enough; otherwise the temp ratio.
        """
        num_of_sample = len(self._sample_ratios)
        # If the number of samples isn't enough,
        # temp_ratio is used as the normal EAR.
        if num_of_sample < self._number_threshold:
            return num_of_sample, self._temp_ratio
        # Sort the ratios and take the mean of the upper 75% as the normal EAR.
        # The lower 25% is not taken under consideration because those may be blinking.
        #
        # Note that we can't sort the samples in-place because we want to keep
        # the recent samples, which is the append order.
        # If the sort is in-place, we don't know which one to pop next time a
        # new sample is appended.
        sorted_samples: List[float] = sorted(self._sample_ratios)
        ratio = statistics.mean(sorted_samples[int(num_of_sample*0.25):])
        return num_of_sample, ratio

    def clear(self) -> None:
        """Clears the existing samples."""
        self._sample_ratios.clear()


class BlinkDetector:
    """Detects whether the eyes are blinking or not by calculating
    the eye aspect ratio (EAR).

    Attributes:
        LEFT_EYE_START_END_IDXS:
            The start and end index (end excluded) which represents the left
            eye in the 68 face landmarks.
        RIGHT_EYE_START_END_IDXS:
            The start and end index (end excluded) which represents the right
            eye in the 68 face landmarks.
    """

    LEFT_EYE_START_END_IDXS:  Tuple[int, int] = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    RIGHT_EYE_START_END_IDXS: Tuple[int, int] = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    def __init__(self, ratio_threshold: float = 0.24) -> None:
        """
        Arguments:
            ratio_threshold:
                An eye aspect ratio lower than this is considered to be a blink.
        """
        self._ratio_threshold = ratio_threshold

    @property
    def ratio_threshold(self) -> float:
        """Returns the ratio threshold used to consider an EAR lower than it
        to be a blink."""
        return self._ratio_threshold

    @ratio_threshold.setter
    def ratio_threshold(self, threshold: float) -> None:
        """
        Arguments:
            threshold:
                An eye aspect ratio lower than this is considered to be a blink.
        """
        self._ratio_threshold = threshold

    @classmethod
    def get_average_eye_aspect_ratio(cls, landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the average EAR from the left and right eye.

        Arguments:
            landmarks: (x, y) coordinates of the 68 face landmarks.
        """
        # use the left and right eye coordinates to compute
        # the eye aspect ratio for both eyes
        left_ratio = BlinkDetector._get_eye_aspect_ratio(cls._extract_eye(landmarks, EyeSide.LEFT))
        right_ratio = BlinkDetector._get_eye_aspect_ratio(cls._extract_eye(landmarks, EyeSide.RIGHT))

        # average the eye aspect ratio together for both eyes
        return statistics.mean((left_ratio, right_ratio))

    def detect_blink(self, landmarks: NDArray[(68, 2), Int[32]]) -> bool:
        """Returns whether the eyes in the face landmarks are blinking or not.

        Arguments:
            landmark: (x, y) coordinates of the 68 face landmarks.
        """
        ratio = BlinkDetector.get_average_eye_aspect_ratio(landmarks)
        return ratio < self._ratio_threshold

    @staticmethod
    def _get_eye_aspect_ratio(eye: NDArray[(6, 2), Int[32]]) -> float:
        """Returns the EAR of eye.

        Eye aspect ratio is the ratio between height and width of the eye.
        EAR = (eye height) / (eye width)
        An opened eye has EAR between 0.2 and 0.4 normaly.

        Arguments:
            eye: (x, y) coordinates of the 6 single eye landmarks.
        """
    	# compute the euclidean distances between the two sets of
    	# vertical eye landmarks (x, y)-coordinates
        vert = []
        vert.append(math.dist(eye[1], eye[5]))
        vert.append(math.dist(eye[2], eye[4]))

        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        hor = []
        hor.append(math.dist(eye[0], eye[3]))

        return statistics.mean(vert) / statistics.mean(hor)

    @classmethod
    def _extract_eye(cls, landmarks: NDArray[(68, 2), Int[32]], side: EyeSide) -> NDArray[(6, 2), Int[32]]:
        """Returns the 6 (x, y) coordinates of landmarks that represent the eye.

        Arguments:
            landmarks: (x, y) coordinates of the 68 face landmarks.
            side: The side of eye to be extracted.
        """
        eye: NDArray[(6, 2), Int[32]]
        if side is EyeSide.LEFT:
            eye = landmarks[cls.LEFT_EYE_START_END_IDXS[0]:cls.LEFT_EYE_START_END_IDXS[1]]
        elif side is EyeSide.RIGHT:
            eye = landmarks[cls.RIGHT_EYE_START_END_IDXS[0]:cls.RIGHT_EYE_START_END_IDXS[1]]
        else:
            raise TypeError(f"type of argument side must be EyeSide, not '{type(side).__name__}'")
        return eye


def draw_landmarks_used_by_blink_detector(
        canvas: ColorImage,
        landmarks: NDArray[(68, 2), Int[32]],
        color: BGR = GREEN) -> ColorImage:
    """Returns the canvas with the eyes' contours.

    Arguments:
        canvas: The image to draw on, it'll be copied.
        landmarks: (x, y) coordinates of the 68 face landmarks.
        color: Color of the lines, green (0, 255, 0) in default.
    """
    canvas_: ColorImage = canvas.copy()

	# compute the convex hull for the left and right eye, then
	# visualize each of the eyes
    for start, end in (BlinkDetector.LEFT_EYE_START_END_IDXS, BlinkDetector.RIGHT_EYE_START_END_IDXS):
        hull = cv2.convexHull(landmarks[start:end])
        cv2.drawContours(canvas_, [hull], -1, color, 1)

    # make lines transparent
    canvas_ = cv2.addWeighted(canvas_, 0.4, canvas, 0.6, 0)
    return canvas_


class AntiNoiseBlinkDetector(QObject):
    """Uses a normal BlinkDetector as its underlayer but noise or face move may
    cause a false-positive "blink".
    So the AntiNoiseBlinkDetector agrees a "blink" only if it continues for a
    sufficient number of frames.

    Attributes:
        EYE_AR_THRESH: The eye aspect ratio to indicate blink.
        EYE_AR_CONSEC_FRAMES:
            The number of consecutive frames the eye must be below the threshold
            to indicate a anti-noise blink.

    Signals:
        s_blinked: Emits everytime a blink is detected.
    """

    s_blinked = pyqtSignal()

    EYE_AR_THRESH: float = 0.24
    EYE_AR_CONSEC_FRAMES: int = 3

    def __init__(self) -> None:
        super().__init__()
        # the underlaying BlinkDetector
        self._blink_detector = BlinkDetector(self.EYE_AR_THRESH)
        self._consec_count: int = 0

    @property
    def blink_detector(self) -> BlinkDetector:
        """Gets the normal BlinkDetector used by AntiNoiseBlinkDetector."""
        return self._blink_detector

    def detect_blink(self, landmarks: NDArray[(68, 2), Int[32]]) -> None:
    	blinked: bool = self._blink_detector.detect_blink(landmarks)
    	if blinked:
    		self._consec_count += 1
    	else:
    		# if the eyes were closed for a sufficient number of frames,
            # it's considered to be a real blink
    		if self._consec_count >= self.EYE_AR_CONSEC_FRAMES:
    			self.s_blinked.emit()
    		self._consec_count = 0


class GoodBlinkRateIntervalDetector(QObject):

    s_good_interval_detected = pyqtSignal(int, int)  # start time, end time

    def __init__(self, good_rate_range: Tuple[float, float]) -> None:
        """
        Arguments:
            good_rate_range: The min and max boundary of the good blink rate (blinks per minute)
        """
        super().__init__()
        self._good_rate_range = good_rate_range
        # time record of blinks
        self._blink_records: List[int] = []

    def add_blink(self) -> None:
        # the time this new blink is made
        time_record = int(time.time())
        # This is a sliding window algorithm.
        #
        # The list "blink records" always contains the blinks within one minute.
        # When adding a new blink makes it exceed one minute, that means its
        # time to check whether that very minute is a good interval or not.
        # If it is, emit the signal to tell there's a good interval and remove
        # the blink records of that minute; if not, pop out the oldest blink
        # record until the list only contains blinks within one minute again.
        if self._blink_records and time_record-self._blink_records[0] > 60:
            if self._good_rate_range[0] <= len(self._blink_records) <= self._good_rate_range[1]:
                self.s_good_interval_detected.emit(self._blink_records[0], self._blink_records[-1])
                self._blink_records.clear()
            else:
                # can't be a good interval, forward the window
                while self._blink_records and time_record-self._blink_records[0] > 60:
                    self._blink_records.pop(0)
        # let this new blink be considered at the next add_blink
        self._blink_records.append(time_record)
