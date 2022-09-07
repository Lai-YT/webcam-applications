from collections import Counter
from typing import List, Tuple

import numpy as np
from sklearn import cluster

# TODO:
# The name CenterCalculator tells nothing about cluster,
# which means it probably violates the SRP.
# (1) calculates center of points
# (2) finds the biggest cluster
#
# Can we use numpy to have the calculation on center of points more straight forward?
class CenterCalculator:
    _LABEL_OF_BIGGEST_CLUSTER: int = 0  # label 0 is the biggest cluster by sklearn
    GOOD_CONCENTATION_CLUSTER_RADIUS: int = 50  # not rigorous

    def __init__(self) -> None:
        # MeanShift fails on non-smooth density data, but it's still good at finding
        # the biggest cluster.
        self._ms = cluster.MeanShift(
            bandwidth=CenterCalculator.GOOD_CONCENTATION_CLUSTER_RADIUS,
            cluster_all=False,
        )

    def fit_points(self, points: List[Tuple[float, float]]) -> None:
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
        return tuple(self._ms.cluster_centers_[CenterCalculator._LABEL_OF_BIGGEST_CLUSTER])  # type: ignore

    @property
    def ratio_of_biggest_cluster(self) -> float:
        count = Counter(self._ms.labels_)
        return count[CenterCalculator._LABEL_OF_BIGGEST_CLUSTER] / len(self._points)
