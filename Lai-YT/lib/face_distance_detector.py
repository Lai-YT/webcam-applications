import cv2
import face_recognition
from typing import Any, List, Optional, Tuple

from .color import *
from .image_type import ColorImage, GrayImage


class FaceDetector:
    """
    This class detects whether there are faces in the image or not.
    It also holds the latest image that passed, so can annotate the face positions.
    """

    def __init__(self) -> None:
        self._frame: Optional[ColorImage] = None
        self._faces: Optional[List[Tuple[int, int, int, int]]] = None

    def refresh(self, frame: ColorImage) -> None:
        """Refreshes the frame and do detection on it.

        Arguments:
            frame (NDArray[(Any, Any, 3), UInt8]): The frame to detect face
        """
        self._frame = frame
        self._faces = self.face_data(frame)

    @property
    def has_face(self) -> bool:
        """Returns if there's a face(s) in the frame."""
        if self._frame is None:
            raise AttributeError("no current frame, please refresh first")
        return len(self._faces) != 0

    @classmethod
    def face_data(cls, frame: ColorImage) -> List[Tuple[int, int, int, int]]:
        """Returns the coordinate and size of the face.

        Arguments:
            frame (NDArray[(Any, Any, 3), UInt8]): The frame to detect face in

        Returns:
            faces (list[tuple(int, int, int, int)]): upper-left x and y, face width and height;
            empty if no face in the frame
        """
        face_locations: List[Tuple[int, int, int, int]] = face_recognition.face_locations(frame)
        faces: List[Tuple[int, int, int, int]] = []
        for face_location in face_locations:
            # this is the return order of face_recognition.face_locations()
            # rearrange since it's not what we want
            up_left_y, low_right_x, low_right_y, up_left_x = face_location
            # x, y, width, height
            faces.append((up_left_x, up_left_y, low_right_x-up_left_x, low_right_y-up_left_y))
        return faces

    def annotated_frame(self, color: BGR = GREEN) -> ColorImage:
        """Returns the frame with the face indicated with angles.

        Arguments:
            color (int, int, int): Color of the lines, green (0, 255, 0) in default
        """
        if self._frame is None:
            raise AttributeError("no current frame, please refresh first")
        frame: ColorImage = self._frame.copy()
        for face in self._faces:
            x, y, w, h = face
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

    def __init__(self, ref_image: ColorImage,
                 face_to_cam_dist: float,
                 face_width: float) -> None:
        """
        Arguments:
            ref_image (NDArray[(Any, Any, 3), UInt8]):
                A reference image to calculate the relation between distance and
                face width
            face_to_cam_dist (float): The distance between face and camera when
                                      taking the reference image
            face_width (float): The actual face width of the user
        """
        faces: List[Tuple[int, int, int, int]] = FaceDetector.face_data(ref_image)
        # there might be many faces in the image, be we only accept single face
        if not faces:
            raise ValueError("can't find any face from the reference image")
        if len(faces) > 1:
            raise ValueError("multiple faces in the reference image, please specify one")
        self._focal: float = self._focal_length(face_to_cam_dist, face_width, faces[0][2])  # 2 is the width in the image
        self._face_width = face_width
        self._distance: Optional[float] = None

    def estimate(self, frame: ColorImage) -> None:
        """Estimates the face distance in the frame.
        It's safe to pass a frame that contains no faces.
        """
        faces: List[Tuple[int, int, int, int]] = FaceDetector.face_data(frame)
        # can't estimate if no face or too many faces
        if not faces or len(faces) > 1:
            self._distance = None
        else:

            self._distance = (self._face_width * self._focal) / faces[0][2]  # take the first and only face, 2 is the width

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
