import cv2
import numpy
from typing import Optional, Tuple

from .color import *


class FaceDetector:
    """
    This class detects whether there's a face in the image or not.
    """

    _classifier = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

    def __init__(self) -> None:
        self._frame: Optional[numpy.ndarray] = None
        self._face: Optional[Tuple[int, int, int, int]] = None

    def refresh(self, frame: numpy.ndarray) -> None:
        """Refreshes the frame and do detection on it.

        Arguments:
            frame (numpy.ndarray): The frame to detect face
        """
        self._frame = frame
        self._face = self.face_data(frame)

    @property
    def has_face(self) -> bool:
        """Returns if there's a face in the frame."""
        return self._face is not None

    @classmethod
    def face_data(cls, frame: numpy.ndarray) -> Optional[Tuple[int, int, int, int]]:
        """Returns the coordinate and size of the face.

        Arguments:
            frame (numpy.ndarray): The frame to detect face in

        Returns:
            face (int, int, int, int): upper-left x and y, face width and height;
            None if no face in the frame
        """
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces: numpy.ndarray = cls._classifier.detectMultiScale(frame, 1.3, 5)

        return None if len(faces) == 0 else tuple(faces[0])

    def annotated_frame(self, *, color: BGR = GREEN) -> numpy.ndarray:
        """Returns the frame with the face indicated with angles.

        Keyword Arguments:
            color (color.BGR): Color of the lines, green (0, 255, 0) in default
        """
        if self._frame is None:
            raise AttributeError("no current frame, please refresh first")
        frame: numpy.ndarray = self._frame.copy()
        if self._face is not None:
            x, y, w, h = self._face
            line_thickness: int = 2
            # affects the length of corner line
            LLV = int(h*0.12)

            # vertical corner lines
            cv2.line(frame, (x, y+LLV), (x+LLV, y+LLV), color, line_thickness)
            cv2.line(frame, (x+w-LLV, y+LLV), (x+w, y+LLV), color, line_thickness)
            cv2.line(frame, (x, y+h), (x+LLV, y+h), color, line_thickness)
            cv2.line(frame, (x+w-LLV, y+h), (x+w, y+h), color, line_thickness)

            # horizontal corner lines
            cv2.line(frame, (x, y+LLV), (x, y+LLV+LLV), color, line_thickness)
            cv2.line(frame, (x+w, y+LLV), (x+w, y+LLV+LLV), color, line_thickness)
            cv2.line(frame, (x, y+h), (x, y+h-LLV), color, line_thickness)
            cv2.line(frame, (x+w, y+h), (x+w, y+h-LLV), color, line_thickness)
        return frame



class DistanceDetector:
    """
    The class knows how wide the face is at a certain distance,
    so can estimate the distance when the face width changes relatively.
    """

    def __init__(self, ref_image: numpy.ndarray,
                 face_to_cam_dist: float,
                 face_width: float) -> None:
        """
        Arguments:
            ref_image (numpy.ndarray): A reference image to calculate the relation
                                       between distance and face width
            face_to_cam_dist (float): The distance between face and camera when
                                      taking the reference image
            face_width (float): The actual face width of the user
        """
        face: Optional[Tuple[int, int, int, int]] = FaceDetector.face_data(ref_image)
        if face is None:
            raise ValueError("can't detect any face from the reference image")
        self._focal: float = self._focal_length(face_to_cam_dist, face_width, face[2])
        self._face_width = face_width
        self._distance: Optional[float] = None

    def estimate(self, frame: numpy.ndarray) -> None:
        """Estimates the face distance in the frame.
        It's safe to pass a frame that contains no faces.
        """
        face: Optional[Tuple[int, int, int, int]] = FaceDetector.face_data(frame)
        if face is None:
            self._distance = None
        else:
            self._distance = (self._face_width * self._focal) / face[2]

    def distance(self) -> Optional[float]:
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
                                         usually get from the face_data method
        """
        return (face_width_in_frame * face_to_cam_dist) / face_width
