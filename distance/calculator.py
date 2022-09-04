import math
from functools import lru_cache
from typing import Any, Final

import cv2
from nptyping import NDArray, Int32

from util.color import BGR, MAGENTA
from util.image_type import ColorImage

_LEFT_ZYGOMATIC_BONE_IDX: Final[int] = 1
_RIGHT_ZYGOMATIC_BONE_IDX: Final[int] = 15

Landmarks = NDArray[Any, Int32]


class FaceDistanceCalculator:
    """
    The class knows how wide the face is at a certain distance,
    so can calculate the distance when the face width changes relatively.
    """

    def __init__(self, ref_landmarks: Landmarks, camera_dist: float) -> None:
        ref_face_width: float = get_face_width(ref_landmarks)
        self._calculator = _FaceDistanceCalculator(ref_face_width, camera_dist)

    def calculate(self, curr_landmarks: Landmarks) -> float:
        curr_face_width: float = get_face_width(curr_landmarks)
        return self._calculator.calculate(curr_face_width)


class _FaceDistanceCalculator:
    def __init__(self, ref_face_width: float, camera_dist: float) -> None:
        self._product: Final[float] = ref_face_width * camera_dist

    @lru_cache
    def calculate(self, curr_face_width: float) -> float:
        curr_distance: float = self._product / curr_face_width
        return curr_distance


def get_face_width(landmarks: Landmarks) -> float:
    """Returns the Euclidean distance between 2 side points of the zygomatic bone.

    Arguments:
        landmarks: (x, y) coordinates of the 68 face landmarks.
    """
    return math.dist(
        landmarks[_LEFT_ZYGOMATIC_BONE_IDX], landmarks[_RIGHT_ZYGOMATIC_BONE_IDX]
    )


# outer util method
def draw_landmarks_used_by_distance_calculator(
    canvas: ColorImage,
    landmarks: Landmarks,
    color: BGR = MAGENTA,
) -> ColorImage:
    """Returns the canvas with 2 side points of the zygomatic bone connected by a transparent line.

    Arguments:
        canvas: The image to draw on, it'll be copied.
        landmarks: (x, y) coordinates of the 68 face landmarks.
        color: Color of the lines, magenta (255, 0, 255) in default.
    """
    canvas_: ColorImage = canvas.copy()

    cv2.line(canvas_, landmarks[1], landmarks[15], color, 2, cv2.LINE_AA)
    # make lines transparent
    canvas_ = cv2.addWeighted(canvas_, 0.4, canvas, 0.6, 0)
    return canvas_
