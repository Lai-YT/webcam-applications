# The 3-layer posture detection refers to
# https://github.com/EE-Ind-Stud-Group/posture-detection

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, cast

import cv2
import mtcnn
from nptyping import Float, Int, NDArray

from concentration.grader import ConcentrationGrader
from posture.calculator import (
    HogAngleCalculator, MtcnnAngleCalculator, PostureLabel, PosturePredictor
)
from sounds.sound_guard import SoundRepeatGuard
from util.image_type import ColorImage
from util.path import to_abs_path


class PostureGuard(SoundRepeatGuard):
    """PostureGuard checks whether the face obtained by landmarks implies a
    good or slump posture.
    """
    def __init__(
            self,
            predictor: PosturePredictor,
            warn_angle: float,
            warning_enabled: bool = True,
            grader: Optional[ConcentrationGrader] = None) -> None:
        """
        Arguments:
            predictor:
                Used to predict the label of image when a clear face isn't found.
            warn_angle:
                Face slope angle larger than this is considered to be a slump posture.
            warning_enabled:
                Whether there's sound that warns the user when a slump posture occurs.
            grader:
                Provide this optional argument if you're using the guard as
                one of the overall concentration grading components. The result
                will be send to the grader.
        """
        super().__init__(
            sound_file=to_abs_path("sounds/posture_slump.wav"),
            interval=8,
            warning_enabled=warning_enabled
        )
        self._hog_layer = _HogLayer(warn_angle)
        self._mtcnn_layer = _MtcnnLayer(warn_angle)
        self._model_layer = _ModelLayer(predictor)
        self._mtcnn_detector = mtcnn.MTCNN()
        self._warn_angle: float = warn_angle
        self._grader: Optional[ConcentrationGrader] = grader

    def set_predictor(self, predictor: PosturePredictor) -> None:
        """
        Arguments:
            predictor: Used to predict the label of image when a clear face isn't found.
        """
        self._model_layer.set_predictor(predictor)

    def set_warn_angle(self, warn_angle: float) -> None:
        """
        Arguments:
            warn_angle: Face slope angle larger than this is considered to be a slump posture.
        """
        self._hog_layer.set_warn_angle(warn_angle)
        self._mtcnn_layer.set_warn_angle(warn_angle)

    def check_posture(
            self,
            frame: ColorImage,
            landmarks: NDArray[(68, 2), Int[32]]) -> Tuple[PostureLabel, str]:
        """Sound plays when is a "slump" posture if warning is enabled.

        Arguments:
            frame: The image contains posture to be predicted.
            landmarks: (x, y) coordinates of the 68 face landmarks.

        Returns:
            The PostureLabel and the detail string of the determination.
            None if any of the necessary attributes aren't set.
        """
        # The posture detection used is made up of 3 layers, which are
        # HOG (Dlib), MTCNN and self-trained model (TensorFlow).
        # HOG is accurate enough and has the fastest speed but needs front faces,
        # so it's used as the first layer; then when the angle is too large that
        # HOG fails, MTCNN takes over. It's robust but so slow that we can't have
        # it as the first layer; last, when the above 2 detections both fail on
        # face detection, we use our model.

        # Get posture label...
        layer: _DetectionLayer
        if landmarks.any():
            # layer 1
            self._hog_layer.detect(landmarks)
            layer = self._hog_layer
        else:
            faces = self._mtcnn_detector.detect_faces(
                cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            )
            if faces:
                # layer 2
                self._mtcnn_layer.detect(faces[0])
                layer = self._mtcnn_layer
            else:
                # layer 3
                self._model_layer.detect(frame)
                layer = self._model_layer

        angle: float
        if isinstance(layer, _AngleLayer) and self._grader is not None:
            self._grader.add_face_center(layer.center)
            angle = layer.angle
        else:  # is model layer
            # XXX: this is a hack to have all layers produce an angle
            angle = 5 if layer.posture is PostureLabel.GOOD else 100

        self._repeat_sound_if(layer.posture is not PostureLabel.GOOD)
        self._send_concentration_info(angle)

        return layer.posture, layer.detail

    def _send_concentration_info(self, angle: float) -> None:
        """Sends a distraction to the grader if the absolute value of angle is
        too large, a concentration otherwise.

        Does nothing if the grader isn't provided.

        Arguments:
            angle: The angle to send info about.
        """
        if self._grader is None:
            return

        TOO_LARGE = 9.2
        if abs(angle) > TOO_LARGE:
            self._grader.add_body_distraction()
        else:
            self._grader.add_body_concentration()


class _DetectionLayer(ABC):
    """All detection layers have a detect method and its posture detection
    result and detail as properties.
    """
    class UndetectedError(ValueError):
        """A getter is called before detection is performed."""
        def __init__(self) -> None:
            self.message = "please detect first"
            super().__init__(self.message)

    def __init__(self) -> None:
        self._posture: Optional[PostureLabel] = None
        self._detail: Optional[str] = None

    @property
    def posture(self) -> PostureLabel:
        if self._posture is None:
            raise _DetectionLayer.UndetectedError
        return self._posture

    @property
    def detail(self) -> str:
        """The detail of the posture detection."""
        if self._detail is None:
            raise _DetectionLayer.UndetectedError
        return self._detail

    @abstractmethod
    def detect(self, target: Any) -> None:
        pass


class _AngleLayer(_DetectionLayer):
    def __init__(self, warn_angle: float) -> None:
        self._warn_angle = warn_angle
        self._angle: Optional[float] = None
        self._center: Optional[Tuple[float, float]] = None

    @property
    def angle(self) -> float:
        if self._angle is None:
            raise _DetectionLayer.UndetectedError
        return self._angle

    @property
    def center(self) -> Tuple[float, float]:
        """The center, precisely nose, of face."""
        if self._center is None:
            raise _DetectionLayer.UndetectedError
        return self._center

    def set_warn_angle(self, warn_angle: float) -> None:
        """
        Arguments:
            warn_angle: Face slope angle larger than this is considered to be a slump posture.
        """
        self._warn_angle = warn_angle

    def _do_angle_check(self) -> None:
        """Determines whether the posture is GOOD or SLUMP with angle
        and tells the detail.
        """
        self._posture = PostureLabel.GOOD
        # calls property for NoneType check
        if abs(self.angle) >= self._warn_angle:
            self._posture = PostureLabel.SLUMP
        self._detail = f"by angle: {round(self.angle, 1)} degrees"


class _HogLayer(_AngleLayer):
    def __init__(self, warn_angle: float) -> None:
        super().__init__(warn_angle)
        self._hog_angle_calculator = HogAngleCalculator()

    def detect(self, landmarks: NDArray[(68, 2), Int[32]]) -> None:
        self._angle = self._hog_angle_calculator.calculate(landmarks)
        self._do_angle_check()
        center = tuple((landmarks[30] + landmarks[33]) / 2)
        if len(center) != 2:
            raise ValueError("landmarks should be 2-dimensional")
        # silence the type check after the length is checked to be 2
        self._center = cast(Tuple[float, float], center)


class _MtcnnLayer(_AngleLayer):
    def __init__(self, warn_angle: float) -> None:
        super().__init__(warn_angle)
        self._mtcnn_angle_calculator = MtcnnAngleCalculator()

    def detect(self, face: Dict) -> None:
        self._angle = self._mtcnn_angle_calculator.calculate(face)
        self._do_angle_check()
        center = tuple(map(float, face["keypoints"]["nose"]))
        if len(center) != 2:
            raise ValueError("face points should be 2-dimensional")
        self._center = cast(Tuple[float, float], center)


class _ModelLayer(_DetectionLayer):
    def __init__(self, predictor: PosturePredictor) -> None:
        super().__init__()
        self._predictor: PosturePredictor = predictor
        self._mtcnn_angle_calculator = MtcnnAngleCalculator()

    def set_predictor(self, predictor: PosturePredictor) -> None:
        """
        Arguments:
            predictor: Used to predict the label of image.
        """
        self._predictor = predictor

    def detect(self, frame: ColorImage) -> None:
        """
        Arguments:
            frame: The image contains posture to be detected.
        """
        conf: Float[32]
        self._posture, conf = self._predictor.predict(frame)
        self._detail = f"by model: {conf:.0%}"
