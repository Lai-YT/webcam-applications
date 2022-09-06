import numpy as np
import pytest

from distance.calculator import (
    _FaceDistanceCalculator,
    FaceDistanceCalculator,
    get_face_width,
)


class Test_FaceDistanceCalculator:
    """Test the calculator which takes face width as parameter."""

    @pytest.fixture
    def calculator(self) -> _FaceDistanceCalculator:
        return _FaceDistanceCalculator(20, 40)

    def test_calculate(self, calculator: _FaceDistanceCalculator) -> None:
        distance: float = calculator.calculate(30)

        assert distance == pytest.approx(26.67, abs=0.01)

    def test_calculate_cache(self, calculator: _FaceDistanceCalculator) -> None:
        distance_1: float = calculator.calculate(30)
        distance_2: float = calculator.calculate(30)

        assert distance_2 == pytest.approx(distance_1)
        assert calculator.calculate.cache_info().hits == 1


class TestFaceDistanceCalculator:
    """Test the calculator which takes face landmarks as parameter."""

    @pytest.fixture
    def calculator(self) -> FaceDistanceCalculator:
        landmarks = np.zeros(shape=(68, 2), dtype=np.int32)
        landmarks[1] = [100, 500]
        landmarks[15] = [300, 550]
        return FaceDistanceCalculator(landmarks, 40)

    def test_calculate(self, calculator: FaceDistanceCalculator) -> None:
        curr_landmarks = np.zeros(shape=(68, 2), dtype=np.int32)
        curr_landmarks[1] = [150, 550]
        curr_landmarks[15] = [300, 550]

        distance: float = calculator.calculate(curr_landmarks)

        assert distance == pytest.approx(54.97, abs=0.01)


def test_get_face_width() -> None:
    landmarks = np.zeros(shape=(68, 2), dtype=np.int32)
    landmarks[1] = [100, 500]
    landmarks[15] = [300, 550]

    width: float = get_face_width(landmarks)

    assert width == pytest.approx(206.16, abs=0.01)
