import math
from typing import Optional

import cv2
from nptyping import Int, NDArray

from lib.color import BGR, MAGENTA
from lib.image_type import ColorImage


class DistanceCalculator:
    """
    The class knows how wide the face is at a certain distance,
    so can calculate the distance when the face width changes relatively.
    """

    def __init__(self, landmarks: NDArray[(68, 2), Int[32]], camera_dist: float) -> None:
        """
        Arguments:
            landmarks: (x, y) coordinates of the 68 face landmarks.
            camera_dist: Distance between face and camera when taking reference image.
        """
        self._product: float = (self._get_face_width(landmarks) * camera_dist)
        self._cache: Optional[float] = None

    def calculate(self, landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the real life distance between face and camera.

        Arguments:
            landmarks: (x, y) coordinates of the 68 face landmarks.
        """
        distance = self._product / self._get_face_width(landmarks)
        self._cache = distance
        return distance

    def distance(self) -> Optional[float]:
        return self._cache

    @staticmethod
    def _get_face_width(landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the Euclidean distance between 2 side points of the zygomatic bone.

        Arguments:
            landmarks: (x, y) coordinates of the 68 face landmarks.
        """
        return math.dist(landmarks[1], landmarks[15])


# outer util method
def draw_landmarks_used_by_distance_calculator(canvas: ColorImage, landmarks: NDArray[(68, 2), Int[32]], color: BGR = MAGENTA) -> ColorImage:
    """Returns the canvas with 2 side points of the zygomatic bone connected by a transparent line.

    Arguments:
        canvas: The image to draw on, it'll be copied.
        landmarks: (x, y) coordinates of the 68 face landmarks.
        color: Color of the lines, magenta (255, 0, 255) in default.
    """
    canvas_ = canvas.copy()

    cv2.line(canvas_, landmarks[1], landmarks[15], color, 2, cv2.LINE_AA)
    # make lines transparent
    canvas_ = cv2.addWeighted(canvas_, 0.4, canvas, 0.6, 0)
    return canvas_
