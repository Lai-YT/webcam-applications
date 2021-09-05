from math import sqrt
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

    def __init__(self, landmarks: NDArray[(68, 2), Int[32]], camera_dist: float, face_width: float) -> None:
        """
        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
            camera_dist (float): Distance between face and camera when taking reference image
            face_width (float): Face width of the user
        """
        self._face_width: float = face_width
        self._focal: float = (self._get_face_width(landmarks) * camera_dist) / face_width
        self._cache: Optional[float] = None

    def calculate(self, landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the real life distance between face and camera.

        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        distance = (self._face_width * self._focal) / self._get_face_width(landmarks)
        self._cache = distance
        return distance

    @property
    def distance(self) -> Optional[float]:
        if self._cache is not None:
            return self._cache

    @staticmethod
    def _get_face_width(landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the Euclidean distance between 2 side points of the zygomatic bone.

        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        x1, y1 = landmarks[1]
        x2, y2 = landmarks[15]
        # Euclidean distance
        return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


# outer util method
def draw_landmarks_used_by_distance_calculator(canvas: ColorImage, landmarks: NDArray[(68, 2), Int[32]], color: BGR = MAGENTA) -> ColorImage:
    """Returns the canvas with 2 side points of the zygomatic bone connected by a transparent line.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to draw on, it'll be copied
        landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        color (int, int, int): Color of the lines, magenta (255, 0, 255) in default
    """
    canvas_ = canvas.copy()

    cv2.line(canvas_, landmarks[1], landmarks[15], color, 2, cv2.LINE_AA)
    # make lines transparent
    canvas_ = cv2.addWeighted(canvas_, 0.4, canvas, 0.6, 0)
    return canvas_
