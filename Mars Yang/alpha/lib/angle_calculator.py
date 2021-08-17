import cv2
import dlib
import math
import warnings
from imutils import face_utils
from nptyping import Int, NDArray
from typing import List

from .color import BGR, GREEN
from .image_type import ColorImage


class AngleCalculator:

    # For dlib’s 68-point facial landmark detector
    NOSE_BRIDGE_IDXS:   List[int] = [27, 30]
    LEFT_EYESIDE_IDXS:  List[int] = [36, 39]
    RIGHT_EYESIDE_IDXS: List[int] = [42, 45]
    MOUTHSIDE_IDXS:     List[int] = [48, 54]

    def calculate(self, shape: dlib.full_object_detection) -> float:
        shape_: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(shape)
        # average the eyes and mouth, they're all horizontal parts
        horizontal: float = (
            (self.angle(shape_[self.RIGHT_EYESIDE_IDXS[0]], shape_[self.RIGHT_EYESIDE_IDXS[1]])
             + self.angle(shape_[self.LEFT_EYESIDE_IDXS[0]], shape_[self.LEFT_EYESIDE_IDXS[1]])
            ) / 2
            + self.angle(shape_[self.MOUTHSIDE_IDXS[0]], shape_[self.MOUTHSIDE_IDXS[1]])
        ) / 2
        vertical: float = self.angle(shape_[self.NOSE_BRIDGE_IDXS[0]], shape_[self.NOSE_BRIDGE_IDXS[1]])
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
        return angle

    @staticmethod
    def angle(p1, p2) -> float:
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


def draw_landmarks_used_by_angle_calculator(canvas: ColorImage, shape: dlib.full_object_detection, color: BGR = GREEN) -> ColorImage:
    """Returns the canvas with the eye sides, mouth side and nose bridge connected by transparent lines.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to draw on, it'll be copied
        shape (dlib.full_object_detection): Landmarks detected by dlib.shape_predictor
        color (int, int, int): Color of the lines, green (0, 255, 0) in default
    """
    canvas_ = canvas.copy()
    shape_: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(shape)

    facemarks_idxs: List[List[int]] = [
        AngleCalculator.LEFT_EYESIDE_IDXS, AngleCalculator.RIGHT_EYESIDE_IDXS,
        AngleCalculator.NOSE_BRIDGE_IDXS, AngleCalculator.MOUTHSIDE_IDXS
    ]
    # connect sides with line
    for facemark in facemarks_idxs:
        cv2.line(
            canvas_,
            shape_[facemark[0]], shape_[facemark[1]],
            color, 2, cv2.LINE_AA
        )
    # make lines transparent
    canvas_ = cv2.addWeighted(canvas_, 0.4, canvas, 0.6, 0)
    return canvas_
