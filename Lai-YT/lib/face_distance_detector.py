import cv2
import numpy
from typing import Tuple, Union


class FaceDistanceDetector:
    """
    The class knows how wide the face is at a certain distance,
    so can estimate the distance when the face width changes relatively.
    """

    # face detector object
    _face_detector = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def __init__(self, ref_image: numpy.ndarray,
                 face_to_cam_dist: float,
                 actual_face_width: float) -> None:
        """
        Arguments:
            ref_img (numpy.ndarray): A reference image to calculate the relation
                                     between distance and face width
            face_to_cam_dist (float): The distance between face and camera when
                                      taking the reference image
            actual_face_width (float): The actual face width of the user
        """
        face_width_in_ref: int = self._face_width(ref_image)
        if face_width_in_ref is None:
            # throw exception
            pass
        self._focal_length: float = (
            self._focal_length(face_to_cam_dist, actual_face_width, face_width_in_ref))
        self._actual_face_width = actual_face_width
        self._distance: float = None

    def estimate(self, frame: numpy.ndarray) -> None:
        """Estimates the face distance in the frame.
        It's safe to pass a frame that contains no faces.
        """
        face_width: int = self._face_width(frame)
        if face_width is None:
            self._distance = None
        else:
            self._distance = (self._actual_face_width * self._focal_length) / face_width

    def distance(self) -> Union[float, None]:
        """Returns the estimated distance between face and camera,
        None if no face in the frame.
        """
        return self._distance

    @staticmethod
    def _focal_length(face_to_cam_dist: float, face_width: float, face_width_in_frame: float) -> float:
        """Returns the distance between lens to CMOS sensor.

        Arguments:
            face_to_cam_dist (float): The distance between face and camera
            face_width (float): The actual face width of the user
            face_width_in_frame (float): Face width in the frame
                                         usually get from the _face_data method
        """
        return (face_width_in_frame * face_to_cam_dist) / face_width

    @classmethod
    def _face_width(cls, frame: numpy.ndarray) -> Union[int, None]:
        """Returns face width in the frame, None if there's no face.

        Arguments:
            frame (numpy.ndarray): The frame to detect face in
        """
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces: Union[ndarray, Tuple] = cls._face_detector.detectMultiScale(frame, 1.3, 5)
        if len(faces) == 0:
            return None
        return faces[0][2]
