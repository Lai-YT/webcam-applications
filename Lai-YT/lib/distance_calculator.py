import cv2
from math import sqrt
from nptyping import Int, NDArray

from .color import BGR, MAGENTA
from .image_type import ColorImage


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
        self._nose_height: float = face_width * (self._get_nose_height(landmarks) / self._get_face_width(landmarks))

    def calculate(self, landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the real life distance between face and camera.

        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        return (self._face_width * self._focal) / self._get_face_width(landmarks)

    @staticmethod
    def _get_face_width(landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the Euclidean distance between 2 side points of the zygomatic bone.

        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        return DistanceCalculator.euclidean_distance(landmarks[1], landmarks[15])

# --- methods for comparison and adjustment ---

    def calculate_by_single_width(self, landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the real life distance between face and camera.

        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        return (self._face_width * self._focal) / self._get_face_width(landmarks)

    def calculate_by_single_height(self, landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the real life distance between face and camera.

        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        return (self._nose_height * self._focal) / self._get_nose_height(landmarks)

    def calculate_by_multiple_weighted(self, landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """Returns the real life distance between face and camera.

        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        by_face_width:  float = (self._face_width * self._focal) / self._get_face_width(landmarks)
        by_nose_height: float = (self._nose_height * self._focal) / self._get_nose_height(landmarks)
        return (by_face_width + by_nose_height) / 2

    @staticmethod
    def _get_nose_height(landmarks: NDArray[(68, 2), Int[32]]) -> float:
        """
        Arguments:
            landmarks (NDArray[(68, 2), Int[32]]): (x, y) coordinates of the 68 face landmarks
        """
        return DistanceCalculator.euclidean_distance(landmarks[27], landmarks[30])

# --- end ---

    @staticmethod
    def euclidean_distance(p1, p2) -> float:
        x1, y1 = p1
        x2, y2 = p2
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
