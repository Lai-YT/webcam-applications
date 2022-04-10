from collections import Counter
from typing import Iterable, Tuple

import numpy as np
from sklearn import cluster


class CenterCalculator:
    # label 0 is the biggest cluster by sklearn
    _LABEL_OF_BIGGEST_CLUSTER = 0

    def __init__(self) -> None:
        # MeanShift fails on non-smooth density data, but it's still good at finding
        # the biggest cluster.
        # I defined the good concentrating cluster to be within a circle of radius 50.
        self._ms = cluster.MeanShift(bandwidth=50, cluster_all=False)

    def fit_points(self, points: Iterable[Tuple[float, float]]) -> None:
        self._points = points
        self._center_of_points: Tuple[float, float] = self._center_of_all_points()
        self._ms.fit(self._points)

    def _center_of_all_points(self) -> Tuple[float, float]:
        x = [p[0] for p in self._points]
        y = [p[1] for p in self._points]
        l = len(self._points)
        return (float(np.sum(x)) / l, float(np.sum(y)) / l)

    @property
    def mean_shift(self) -> cluster.MeanShift:
        return self._ms

    @property
    def center_of_points(self) -> Tuple[float, float]:
        return self._center_of_points

    @property
    def center_of_biggest_cluster(self) -> Tuple[float, float]:
        return tuple(self._ms.cluster_centers_[CenterCalculator._LABEL_OF_BIGGEST_CLUSTER])

    @property
    def ratio_of_biggest_cluster(self) -> float:
        count = Counter(self._ms.labels_)
        return count[0] / len(self._points)
