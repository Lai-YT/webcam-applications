import math
import warnings
from typing import List, Optional

import cv2
from nptyping import Int, NDArray

from lib.color import BGR, GREEN
from lib.image_type import ColorImage


class AngleCalculator:

    # For dlib’s 68-point facial landmark detector
    NOSE_BRIDGE_IDXS:   List[int] = [27, 30]
    LEFT_EYESIDE_IDXS:  List[int] = [36, 39]
    RIGHT_EYESIDE_IDXS: List[int] = [42, 45]
    MOUTHSIDE_IDXS:     List[int] = [48, 54]

    def __init__(self) -> None:
        self._cache: Optional[float] = None

    def calculate(self, landmarks: NDArray[(68, 2), Int[32]]) -> float:
        # average the eyes and mouth, they're all horizontal parts
        horizontal: float = (
            (AngleCalculator.angle_between(landmarks[self.RIGHT_EYESIDE_IDXS[0]], landmarks[self.RIGHT_EYESIDE_IDXS[1]])
             + AngleCalculator.angle_between(landmarks[self.LEFT_EYESIDE_IDXS[0]], landmarks[self.LEFT_EYESIDE_IDXS[1]])
            ) / 2
            + AngleCalculator.angle_between(landmarks[self.MOUTHSIDE_IDXS[0]], landmarks[self.MOUTHSIDE_IDXS[1]])
        ) / 2
        vertical: float = AngleCalculator.angle_between(landmarks[self.NOSE_BRIDGE_IDXS[0]], landmarks[self.NOSE_BRIDGE_IDXS[1]])
        # Under normal situations (not so close to the middle line):
        # If skews right, horizontal is positive, vertical is negative, e.g., 15 and -75;
        # if skews left, horizontal is negative, vertical is positive, e.g., -15 and 75.
        # Sum of their absolute value is approximately 90 (usually a bit larger).

        # When close to the middle, it's possible that both values are of the
        # same sign.

        # Horizontal value is already what we want, vertical value needs to be adjusted.
        # And again, we take their average
        angle: float = (
            (horizontal + (vertical + 90.0)) / 2
            if vertical < 0 else
            (horizontal + (vertical - 90.0)) / 2
        )
        self._cache = angle
        return angle

    @staticmethod
    def angle_between(p1, p2) -> float:
        """Returns the included angle of the vector p2 - p1 in degree.
        Between (-90.0, 90.0].

        Arguments:
            p1 (a subscriptable object that contains 2 int elements)
            p2 (a subscriptable object that contains 2 int elements)
        """
        x1 ,y1 = p1
        x2 ,y2 = p2
        with warnings.catch_warnings():
            # RuntimeWarning: divide by zero encountered in long_scalars
            # Ignore possible warning when 90.0
            warnings.simplefilter("ignore", category=RuntimeWarning)
            return math.atan((y2 - y1) / (x2 - x1)) * 180 / math.pi

    def angle(self) -> Optional[float]:
        if self._cache is not None:
            return self._cache


def draw_landmarks_used_by_angle_calculator(canvas: ColorImage, landmarks: NDArray[(68, 2), Int[32]], color: BGR = GREEN) -> ColorImage:
    """Returns the canvas with the eye sides, mouth side and nose bridge connected by transparent lines.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to draw on, it'll be copied
        landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        color (int, int, int): Color of the lines, green (0, 255, 0) in default
    """
    canvas_ = canvas.copy()

    facemarks_idxs: List[List[int]] = [
        AngleCalculator.LEFT_EYESIDE_IDXS, AngleCalculator.RIGHT_EYESIDE_IDXS,
        AngleCalculator.NOSE_BRIDGE_IDXS, AngleCalculator.MOUTHSIDE_IDXS
    ]
    # connect sides with line
    for facemark in facemarks_idxs:
        cv2.line(
            canvas_,
            landmarks[facemark[0]], landmarks[facemark[1]],
            color, 2, cv2.LINE_AA
        )
    # make lines transparent
    canvas_ = cv2.addWeighted(canvas_, 0.4, canvas, 0.6, 0)
    return canvas_
