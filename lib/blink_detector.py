# reference:
# https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/

import statistics
from enum import Enum, auto
from typing import Optional, Tuple

import cv2
from imutils import face_utils
from nptyping import Int, NDArray
from scipy.spatial import distance as dist

from lib.color import BGR, GREEN
from lib.image_type import ColorImage


class EyeSide(Enum):
    LEFT = auto()
    RIGHT = auto()


class _SelfAdjustmentNormalEyeAspectRatioMaker:
    """Take a certain number of frames that contains face to determine
    the normal EAR of the user.
    """
    def __init__(
            self,
            temp_ratio: float = 0.3,
            number_threshold: int = 100) -> None:
        """
        temp_ratio is used before the normal EAR is determined.
        """
        if temp_ratio < 0.15 or temp_ratio > 0.5:
            raise ValueError("normal eye aspect ratio should >= 0.15 and <= 0.5")
        if number_threshold < 100:
            raise ValueError("number of samples under 100 makes the normal eye aspect ratio susceptible to extreme values")

        self._temp_ratio = temp_ratio
        self._number_threshold = number_threshold
        self._sample_ratios = []

    def read_sample(self, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        """Adds a new sample of EAR."""
        # Empty landmarks is not count.
        if not landmarks.any():
            return
        self._sample_ratios.append(BlinkDetector.get_average_eye_aspect_ratio(landmarks))

    def get_normal_ratio(self) -> Tuple[int, float]:
        """Returns the self-adjustment EAR when the number of sample ratio is
        enough; otherwise the temp ratio.
        """
        num_of_sample = len(self._sample_ratios)
        # If the number of samples isn't enough,
        # temp_ratio is used as the normal EAR.
        if num_of_sample < self._number_threshold:
            return num_of_sample, self._temp_ratio
        # Sort the ratios and take the mean of the upper 75% as the normal EAR.
        # The lower 25% is not taken under consideration because those may be blinking.
        self._sample_ratios.sort()
        ratio = statistics.mean(self._sample_ratios[int(num_of_sample*0.25):])
        return num_of_sample, ratio


class BlinkDetector:
    """Detects whether the eyes are blinking or not by calculating
    the eye aspect ratio (EAR).
    """

    LEFT_EYE_START_END_IDXS = face_utils.FACIAL_LANDMARKS_IDXS["left_eye"]
    RIGHT_EYE_START_END_IDXS = face_utils.FACIAL_LANDMARKS_IDXS["right_eye"]

    def __init__(self, ratio_threshold: Optional[float] = None) -> None:
        """
        Arguments:
            ratio_threshold:
                An eye aspect ratio lower than this is considered to be blinked.
                If not given, the threshold is determined by algorithm.
        """
        if ratio_threshold is None:
            self._ratio_maker = _SelfAdjustmentNormalEyeAspectRatioMaker(0.3, 500)
        else:
            self._ratio_threshold = ratio_threshold

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
        ratio = statistics.mean((left_ratio, right_ratio))
        return ratio

    def detect_blink(self, landmarks: NDArray[(68, 2), Int[32]]) -> bool:
        """Returns whether the eyes in the face landmarks are blinking or not.

        Arguments:
            landmark: (x, y) coordinates of the 68 face landmarks.
        """
        # Keep feeding samples if a algorithm-based threshold is used
        # and not yet determined.
        if hasattr(self, "_ratio_maker"):
            self._ratio_maker.read_sample(landmarks)

        ratio = BlinkDetector.get_average_eye_aspect_ratio(landmarks)
        return ratio < self._get_ratio_threshold()

    def _get_ratio_threshold(self) -> float:
        # If an algorithm-based threshold is used,
        # first get the normal EAR from maker,
        # then has 0.85 of it as the threshold.
        if hasattr(self, "_ratio_maker"):
            num, ratio = self._ratio_maker.get_normal_ratio()
            threshold = ratio * 0.85
            if num >= 500:
                self._ratio_threshold = threshold
                # The threshold is determined, maker is not needed any more.
                del self._ratio_maker
            return threshold
        return self._ratio_threshold

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
        vert.append(dist.euclidean(eye[1], eye[5]))
        vert.append(dist.euclidean(eye[2], eye[4]))

        # compute the euclidean distance between the horizontal
        # eye landmark (x, y)-coordinates
        hor = []
        hor.append(dist.euclidean(eye[0], eye[3]))

        # compute the eye aspect ratio
        ratio = statistics.mean(vert) / statistics.mean(hor)

        # return the eye aspect ratio
        return ratio

    @classmethod
    def _extract_eye(cls, landmarks: NDArray[(68, 2), Int[32]], side: EyeSide) -> NDArray[(6, 2), Int[32]]:
        """Returns the 6 (x, y) coordinates of landmarks that represent the eye.

        Arguments:
            landmarks: (x, y) coordinates of the 68 face landmarks.
            side: The side of eye to be extracted.
        """
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
    canvas_ = canvas.copy()

	# compute the convex hull for the left and right eye, then
	# visualize each of the eyes
    for start, end in (BlinkDetector.LEFT_EYE_START_END_IDXS, BlinkDetector.RIGHT_EYE_START_END_IDXS):
        hull = cv2.convexHull(landmarks[start:end])
        cv2.drawContours(canvas_, [hull], -1, color, 1)

    # make lines transparent
    canvas_ = cv2.addWeighted(canvas_, 0.4, canvas, 0.6, 0)
    return canvas_
