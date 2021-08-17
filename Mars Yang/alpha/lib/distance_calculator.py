import cv2
import dlib
from imutils import face_utils
from math import sqrt
from nptyping import Int, NDArray

from .color import BGR, MAGENTA
from .image_type import ColorImage


class DistanceCalculator:
    def __init__(self, shape: dlib.full_object_detection, camera_dist: float, face_width: float) -> None:
        """
        Arguments:
            shape (dlib.full_object_detection):
                The landmarks of the reference image, detected by dlib.shape_predictor
            camera_dist (float): Distance between face and camera when taking reference image
            face_width (float): Face width of the user
        """
        self._face_width: float = face_width
        self._focal: float = (self._get_face_width(shape) * camera_dist) / face_width

    def calculate(self, shape: dlib.full_object_detection) -> float:
        return (self._face_width * self._focal) / self._get_face_width(shape)

    @staticmethod
    def _get_face_width(shape: dlib.full_object_detection) -> float:
        """Returns triple length of nose bridge."""
        shape_: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(shape)
        x1, y1 = shape_[28]
        x2, y2 = shape_[31]
        return 3 * sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
        # """Returns the Euclidean distance between 2 side points of the zygomatic bone."""
        # shape_: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(shape)
        # x1, y1 = shape_[1]
        # x2, y2 = shape_[15]
        # return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def draw_landmarks_used_by_distance_calculator(canvas: ColorImage, shape: dlib.full_object_detection, color: BGR = MAGENTA) -> ColorImage:
    """Returns the canvas with 2 side points of the zygomatic bone connected by a transparent line.

    Arguments:
        canvas (NDArray[(Any, Any, 3), UInt8]): The image to draw on, it'll be copied
        shape (dlib.full_object_detection): Landmarks detected by dlib.shape_predictor
        color (int, int, int): Color of the lines, magenta (255, 0, 255) in default
    """
    canvas_ = canvas.copy()
    shape_: NDArray[(68, 2), Int[32]] = face_utils.shape_to_np(shape)

    cv2.line(canvas_, shape_[1], shape_[15], color, 2, cv2.LINE_AA)

    # make lines transparent
    canvas_ = cv2.addWeighted(canvas_, 0.4, canvas, 0.6, 0)
    return canvas_
