import math
import re
import sys
import time
from pathlib import Path
from typing import List, Tuple

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np

from face_center.calculator import CenterCalculator


def main(target: Path) -> None:
    face_centers: List[Tuple[float, float]] = []
    with target.open("r") as f:
        pattern = re.compile(r"[()\n]")  # no "(", ")" and "\n"
        for line in f:
            x, y = map(float, pattern.sub("", line).split(", "))
            face_centers.append((x, y))

    # make np array so easy compute
    all_cents = np.array(face_centers)
    print(f"number of faces: {len(all_cents)}")

    calculator = CenterCalculator()

    print(calculator.mean_shift)
    # You'll see that MeanShift has high time complexity, O(T*n*log(n)),
    # T is the number of samples to fit with, here, T = n.
    t = time.perf_counter()
    calculator.fit_points(all_cents)
    print(f"elapsed time: {time.perf_counter() - t}")
    centers = calculator.mean_shift.cluster_centers_
    labels = calculator.mean_shift.labels_

    fig, ax = plt.subplots()
    # select the leading colors
    colors = list(mcolors.BASE_COLORS.values())[:len(centers)]

    for k, (cluster_center, color) in enumerate(zip(centers, colors)):
        ax.scatter(all_cents[labels == k, 0], all_cents[labels == k, 1],
                   color=color, alpha=0.5)
        ax.scatter(*cluster_center, color="w", edgecolor=color)
    # noises
    ax.scatter(all_cents[labels == -1, 0], all_cents[labels == -1, 1],
               color=mcolors.CSS4_COLORS["dodgerblue"], alpha=0.5, label="noise")
    # center of all points
    ax.scatter(*calculator.center_of_points, color="m", edgecolor="k", label="all center")

    dist = math.dist(calculator.center_of_points, calculator.center_of_biggest_cluster)
    print(f"{calculator.ratio_of_biggest_cluster:.2f} in the biggest cluster")
    print(f"{dist:.2f} far from the center of all points")
    plt.text(50, 50, f"ratio: {calculator.ratio_of_biggest_cluster:.2f}; dist: {dist:.2f}")

    ax.legend()

    # y-axis is flipped
    ax.set(xlim=(0, 640), ylim=(480, 0))
    ax.xaxis.set_ticks_position("top")

    plt.show()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError(f"\n\t usage: python {__file__} $(file_to_plot)")

    main(Path.cwd() / sys.argv[1])
