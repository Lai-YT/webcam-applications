"""Deprecated, only for comparison test in dist_compare.py."""

from nptyping import NDArray, Int
from typing import Optional

from .face_detector import FaceDetector
from .image_type import ColorImage


class DistanceDetector:
    """
    The class knows how wide the face is at a certain distance,
    so can estimate the distance when the face width changes relatively.
    """

    def __init__(self, ref_image: ColorImage,
                 camera_dist: float,
                 face_width: float) -> None:
        """
        Arguments:
            ref_image (NDArray[(Any, Any, 3), UInt8]):
                A reference image to calculate the relation between distance and
                face width
            camera_dist (float):
                The distance between face and camera when taking
                the reference image
            face_width (float): The actual face width of the user
        """
        faces: NDArray[(Any, 4), Int] = FaceDetector.face_data(ref_image)
        # there might be many faces in the image, be we only accept single face
        if not len(faces):
            raise ValueError("can't find any face from the reference image")
        if len(faces) > 1:
            raise ValueError("multiple faces in the reference image, please specify one")
        self._focal: float = (faces[0][2] * camera_dist) / face_width # 2 is the width in the image
        self._face_width = face_width
        self._distance: Optional[float] = None

    def estimate(self, frame: ColorImage) -> None:
        """Estimates the face distance in the frame.
        It's safe to pass a frame that contains no faces.
        """
        faces: NDArray[(Any, 4), Int] = FaceDetector.face_data(frame)
        # can't estimate if no face or too many faces
        if len(faces) != 1:
            self._distance = None
        else:
            self._distance = (self._face_width * self._focal) / faces[0][2]  # take the first and only face, 2 is the width

    def distance(self) -> Optional[float]:
        """Returns the estimated distance between face and camera,
        None if no face in the frame.
        """
        return self._distance
