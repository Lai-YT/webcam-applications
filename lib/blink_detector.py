# Reference:
#   Adrian Rosebrock. Eye blink detection with OpenCV, Python, and dlib (2016)
#   https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/
#
#   Ali A Abusharha. Changes in blink rate and ocular symptoms during different reading tasks (2017)
#   https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6118863/
#    Several studies have investigated the blink rate and the interval between
#    blinks. It has been reported that the normal spontaneous blink rate is
#    between 12 and 15/min[1]. Other studies showed that the interval between blinks
#    ranges from 2.8 to 4 and from 2 to 10 s. A mean blink rate of up to 22 blinks/min
#    has been reported under relaxed conditions.
#
#   [1] M J Doughty. Consideration of three types of spontaneous eyeblink
#       activity in normal humans: during reading and video display terminal use,
#       in primary gaze, and while in conversation (2010)
#       https://pubmed.ncbi.nlm.nih.gov/11700965/#affiliation-1
#        Spontaneous eyeblink rate, SEBR.
#        Statistical analysis (with calculation of 95% confidence interval values)
#        indicate that reading-SEBR should be between 1.4 and 14.4 eyeblinks/min,
#        primary gaze-SEBR between 8.0 and 21.0 eyeblinks/min and conversational-SEBR
#        between 10.5 and 32.5 eyeblinks/min for normal adults.


import math
import time
import statistics
from collections import deque
from enum import Enum, auto
from typing import Deque, List, Tuple

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
            number_threshold: Higher number of samples than this is considered to be reliable.
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
        if not landmarks.any():
            raise ValueError("landmarks should represent a face")

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

    Signals:
        s_blinked: Emits everytime a blink is detected.
    """

    s_blinked = pyqtSignal()

    def __init__(self, ratio_threshold: float = 0.24, consec_frame: int = 3) -> None:
        """
        Arguments:
            ratio_threshold: The eye aspect ratio to indicate blink.
            consec_frame:
                The number of consecutive frames the eye must be below the threshold
                to indicate an anti-noise blink.
        """
        super().__init__()
        # the underlaying BlinkDetector
        self._base_detector = BlinkDetector(ratio_threshold)
        self._consec_frame = consec_frame
        self._consec_count: int = 0

    @property
    def ratio_threshold(self) -> float:
        """Returns the ratio threshold used to consider an EAR lower than it
        to be a blink with noise."""
        return self._base_detector.ratio_threshold

    @ratio_threshold.setter
    def ratio_threshold(self, threshold: float) -> None:
        """
        Arguments:
            threshold:
                An eye aspect ratio lower than this is considered to be a blink with noise.
        """
        self._base_detector.ratio_threshold = threshold

    def detect_blink(self, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Uses the base detector with EYE_AR_CONSEC_FRAMES to determine whether
        there's an anti-noise blink.

        Emits:
            s_blinked: Emits when a anti-noise blink is detected.
        """
        blinked: bool = self._base_detector.detect_blink(landmarks)
        if blinked:
           self._consec_count += 1
        else:
            # if the eyes were closed for a sufficient number of frames,
            # it's considered to be a real blink
            if self._consec_count >= self._consec_frame:
                self.s_blinked.emit()
            self._consec_count = 0


class GoodBlinkRateIntervalDetector(QObject):
    """Detects whether the blink rate is in the good rate range or not.

    The number of blinks per minute is the blink rate, which is an integer here
    since it counts but does not take the average.

    Signals:
        s_good_interval_detected:
            Emits when a good blink rate is detected.
            It sends the first time (FT) of the blinks in that minute,
            which implies [FT, FT+60] as the interval, and the blink rate of
            that minute.
    """

    s_good_interval_detected = pyqtSignal(int, int)  # start time, rate

    def __init__(self, good_rate_range: Tuple[int, int] = (15, 25)) -> None:
        """
        Arguments:
            good_rate_range:
                The min and max boundary of the good blink rate (blinks per minute).
                It's not about the average rate, so both are with type int.
                15 ~ 25 in default. For a proper blink rate, one may refer to
                https://pubmed.ncbi.nlm.nih.gov/11700965/#affiliation-1
        """
        super().__init__()
        self._good_rate_range = good_rate_range
        # Time record of blinks.
        # The length of it also indicates how many blinks there are within the
        # time between index 0 and -1.
        self._blink_times: Deque[int] = deque()

    def check_blink_rate(self) -> None:
        """Checks whether there's a good interval.

        Call this method manually to have the detector follow the current time.
        Emits:
            s_good_interval_detected:
                Emits when there's a good interval.
                Sends the start time and the blink rate.
        """
        # This is a sliding window algorithm.
        #
        # The deque "blink times" always contains the blinks within this very minute.
        # When the time length invloved by current and the earliest time, that
        # means it's time to check whether this very minute is a good interval or not.
        # If it is, emit the signal to tell there's a good interval and remove
        # the blink records of that minute; if not, pop out the oldest blink
        # record until the deque only contains blinks within one minute again.
        current_time = int(time.time())
        if self._blink_times and (current_time - self._blink_times[0]) > 60:
            blink_rate: int = len(self._blink_times)
            if self._good_rate_range[0] <= blink_rate <= self._good_rate_range[1]:
                self.s_good_interval_detected.emit(self._blink_times[0], blink_rate)
                self._blink_times.clear()
            else:
                # can't be a good interval, forward the window
                while (self._blink_times
                        and (current_time - self._blink_times[0]) > 60):
                    self._blink_times.popleft()

    def add_blink(self) -> None:
        """Adds a new time of blink and checks whether there's a good interval.

        Emits:
            s_good_interval_detected:
                Emits when there's a good interval.
                Sends the start time and the blink rate.
        """
        self._blink_times.append(int(time.time()))
        self.check_blink_rate()
