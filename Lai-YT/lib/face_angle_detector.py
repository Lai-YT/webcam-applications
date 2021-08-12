# tutorial to refer to:
# https://www.pyimagesearch.com/2017/04/03/facial-landmarks-dlib-opencv-python/

import cv2
import dlib
import math
import warnings
from imutils import face_utils
from nptyping import Int, NDArray
from typing import List, Optional

from .color import BGR, GREEN
from .image_type import ColorImage
from .path import to_abs_path


class FaceAngleDetector:

    # For dlib’s 68-point facial landmark detector
    NOSE_BRIDGE_IDXS:   List[int] = [27, 30]
    LEFT_EYESIDE_IDXS:  List[int] = [36, 39]
    RIGHT_EYESIDE_IDXS: List[int] = [42, 45]
    MOUTHSIDE_IDXS:     List[int] = [48, 54]

    _detector = dlib.get_frontal_face_detector()
    _predictor = dlib.shape_predictor(
        to_abs_path('trained_models/shape_predictor_68_face_landmarks.dat')
    )

    def __init__(self) -> None:
        self._frame: Optional[ColorImage] = None
        self._shapes: Optional[List[NDArray[(68, 2), Int[32]]]] = None
        self._angles: Optional[List[float]]  = None

    def refresh(self, frame: ColorImage) -> None:
        """Refreshes the frame and analyzes it.

        Arguments:
            frame (NDArray[(Any, Any, 3), UInt8]): The frame to analyze
        """
        self._frame = frame
        self._analyze()

    def _analyze(self) -> None:
        """Calculates the angle (degree) of the faces.
        """
        faces = self._detector(self._frame)
        shapes: List[NDArray[(68, 2), Int[32]]] = []

        for face in faces:
            shapes.append(face_utils.shape_to_np(self._predictor(self._frame, face)))
        self._shapes = shapes

        angles: List[float] = []
        for shape in shapes:
            # average the eyes and mouth, they're all horizontal parts
            horizontal: float = (
                (self.angle(shape[self.RIGHT_EYESIDE_IDXS[0]], shape[self.RIGHT_EYESIDE_IDXS[1]])
                 + self.angle(shape[self.LEFT_EYESIDE_IDXS[0]], shape[self.LEFT_EYESIDE_IDXS[1]])
                ) / 2
                + self.angle(shape[self.MOUTHSIDE_IDXS[0]], shape[self.MOUTHSIDE_IDXS[1]])
            ) / 2
            vertical: float = self.angle(shape[self.NOSE_BRIDGE_IDXS[0]], shape[self.NOSE_BRIDGE_IDXS[1]])
            # Under normal situations (not so close to the middle line):
            # If skews right, horizontal is positive, vertical is negative, e.g., 15 and -75;
            # if skews left, horizontal is negative, vertical is positive, e.g., -15 and 75.
            # Sum of their absolute value is approximately 90 (usually a bit larger).

            # When close to the middle, it's possible that both values are of the
            # same sign.

            # Horizontal value is already what we want, vertical value needs to be adjusted.
            # And again, we take their average.
            angles.append(
                (horizontal + (vertical + 90.0)) / 2
                if vertical < 0 else
                (horizontal + (vertical - 90.0)) / 2
            )
        self._angles = angles

    def angles(self) -> List[float]:
        """Returns the angle (degree) of the faces.
        Included angle is between the vertical line of the frame and the vertical
        middle line of the face. Positive angle indicates a right skew.
        """
        if self._angles is None:
            raise AttributeError("no current frame, please refresh first")
        return self._angles

    def mark_facemarks(self, canvas: ColorImage = None, color: BGR = GREEN) -> ColorImage:
        """Returns the frame with the eye sides, mouth side and nose bridge marked.

        Arguments:
            canvas (NDArray[(Any, Any, 3), UInt8]):
                The frame that you want to mark on, it'll be copied.
                The frame passed to refresh in default.
            color (int, int, int): Color of the lines, green (0, 255, 0) in default
        """
        if self._frame is None or self._shapes is None:
            raise AttributeError("no current frame, please refresh first")

        if canvas is None:
            canvas = self._frame.copy()
        frame: ColorImage = canvas.copy()

        for shape in self._shapes:
            cv2.line(
                canvas,
                shape[self.LEFT_EYESIDE_IDXS[0]], shape[self.LEFT_EYESIDE_IDXS[1]],
                color, 2, cv2.LINE_AA
            )
            cv2.line(
                canvas,
                shape[self.RIGHT_EYESIDE_IDXS[0]], shape[self.RIGHT_EYESIDE_IDXS[1]],
                color, 2, cv2.LINE_AA
            )
            cv2.line(
                canvas,
                shape[self.NOSE_BRIDGE_IDXS[0]], shape[self.NOSE_BRIDGE_IDXS[1]],
                color, 2, cv2.LINE_AA
            )
            cv2.line(
                canvas,
                shape[self.MOUTHSIDE_IDXS[0]], shape[self.MOUTHSIDE_IDXS[1]],
                color, 2, cv2.LINE_AA
            )
        # make lines transparent
        canvas = cv2.addWeighted(canvas, 0.4, frame, 0.6, 0)
        return canvas

    @staticmethod
    def angle(p1, p2) -> float:
        """Returns the included angle of the vector p2 - p1 in degree.
        Between (-90.0, 90.0].

        Arguments:
            p1 (a subscriptable object that contains 2 int elements)
            p2 (a subscriptable object that contains 2 int elements)
        """
        x1 ,y1 = p1
        x2 ,y2 = p2
        with warnings.catch_warnings():
            # RuntimeWarning: divide by zero encountered in long_scalars
            # Ignore possible warning when 90.0
            warnings.simplefilter("ignore", category=RuntimeWarning)
            return math.atan((y2 - y1) / (x2 - x1)) * 180 / math.pi
