import cv2
from nptyping import Int, NDArray, UInt8
from typing import Any, Optional, Tuple

from .color import BGR, GREEN
from .image_type import ColorImage, GrayImage
from .path import to_abs_path


class FaceDetector:
    """
    This class detects whether there are faces in the image or not.
    It also holds the latest image that passed, so can annotate the face positions.
    """

    _frontal_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    # note that profileface only detects real live left-turned faces
    _side_detector = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")

    def __init__(self) -> None:
        self._frame: Optional[ColorImage] = None
        self._faces: Optional[NDArray[(Any, 4), Int]] = None

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

    def mark_face(self, canvas: ColorImage = None, color: BGR = GREEN) -> ColorImage:
        """Returns the frame with the face indicated with angles.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]):
                The frame that you want to mark on, it'll be copied.
                The frame passed to refresh in default.
            color (int, int, int): Color of the lines, green (0, 255, 0) in default
        """
        if self._frame is None:
            raise AttributeError("no current frame, please refresh first")

        if canvas is None:
            canvas = self._frame.copy()
        frame: ColorImage = canvas.copy()

        for x, y, w, h in self._faces:
            line_thickness: int = 2
            # affects the length of corner line
            LLV = int(h*0.12)

            # vertical corner lines
            cv2.line(canvas, (x, y+LLV), (x+LLV, y+LLV), color, line_thickness)
            cv2.line(canvas, (x+w-LLV, y+LLV), (x+w, y+LLV), color, line_thickness)
            cv2.line(canvas, (x, y+h), (x+LLV, y+h), color, line_thickness)
            cv2.line(canvas, (x+w-LLV, y+h), (x+w, y+h), color, line_thickness)

            # horizontal corner lines
            cv2.line(canvas, (x, y+LLV), (x, y+LLV+LLV), color, line_thickness)
            cv2.line(canvas, (x+w, y+LLV), (x+w, y+LLV+LLV), color, line_thickness)
            cv2.line(canvas, (x, y+h), (x, y+h-LLV), color, line_thickness)
            cv2.line(canvas, (x+w, y+h), (x+w, y+h-LLV), color, line_thickness)
        return canvas

    @classmethod
    def face_data(cls, frame: ColorImage) -> NDArray[(Any, 4), Int]:
        """Returns the coordinate and size of the faces.
        Using OpenCV library.
        Note that the meaning of face width changes when it's a side face.

        Arguments:
            frame (NDArray[(Any, Any, 3), UInt8]): The frame to detect face in

        Returns:
            face (NDArray[(Any, 4), Int]): upper-left x and y, face width and height;
            empty if no face in the frame
        """
        frame: GrayImage = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # detection parameters:
        scale_factor: float = 1.2
        min_neighbors: int = 5
        min_size: Tuple[int, int] = (150, 150)
        # frontal face detection first
        faces: NDArray[(Any, 4), Int] = cls._frontal_detector.detectMultiScale(
            frame, scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=min_size
        )
        # might be a side face when frontal detector has no result,
        # turn to use the side face detector
        if len(faces) == 0:
            faces = cls._side_detector.detectMultiScale(
                frame, scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=min_size
            )
        # and flip the frame horizontaly to try each side of the face
        if len(faces) == 0:
            faces = cls._side_detector.detectMultiScale(
                cv2.flip(frame, flipCode=1), scaleFactor=scale_factor, minNeighbors=min_neighbors, minSize=min_size
            )
            if len(faces) != 0:
                # Since the frame is fliped, x coordinates aren't correct.
                # number of columns is the width
                _, frame_width = frame.shape
                for face in faces:
                    # now is correct upper "right" corner
                    face[0] = frame_width - face[0]
                    # to upper "left" corner
                    face[0] -= face[2]
        return faces
