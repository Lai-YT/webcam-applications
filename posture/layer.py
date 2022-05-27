from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple, cast

from nptyping import Int, NDArray

from posture.calculator import HogAngleCalculator, MtcnnAngleCalculator, PostureLabel


class DetectionLayer(ABC):
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
            raise DetectionLayer.UndetectedError
        return self._posture

    @property
    def detail(self) -> str:
        """The detail of the posture detection."""
        if self._detail is None:
            raise DetectionLayer.UndetectedError
        return self._detail

    @abstractmethod
    def detect(self, target: Any) -> None:
        pass


class AngleLayer(DetectionLayer):
    """A layer that detects face to get angle and center of face."""

    def __init__(self, warn_angle: float) -> None:
        self._warn_angle = warn_angle
        self._angle: Optional[float] = None
        self._center: Optional[Tuple[float, float]] = None

    @property
    def angle(self) -> float:
        if self._angle is None:
            raise DetectionLayer.UndetectedError
        return self._angle

    @property
    def center(self) -> Tuple[float, float]:
        """The center, precisely nose, of face."""
        if self._center is None:
            raise DetectionLayer.UndetectedError
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


class HogLayer(AngleLayer):
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


class MtcnnLayer(AngleLayer):
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
