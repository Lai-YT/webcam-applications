import math
import sys
import time
from ast import literal_eval as make_tuple
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from sklearn import cluster

'''centroid is about face, center is about centroid points'''

def get_center_of_group(points) -> Tuple[float, float]:
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    l = len(points)
    return (np.sum(x) / l, np.sum(y) / l)


def main(target: Path) -> None:
    # "all" keeps the order
    centroids: Dict[str, List[float]] = {"hog": [], "mtcnn": [], "all": []}
    with target.open("r") as f:
        for line in f:
            line = line.rstrip("\n")
            cat, centroid = line.split(" ", 1)
            centroid = make_tuple(centroid)
            centroids[cat].append(centroid)
            centroids["all"].append(centroid)

    # make np array so easy compute
    all_cents = np.array(centroids["all"])
    print(f"number of faces: {len(all_cents)}")

    # MeanShift fails on non-smooth density data, but it's still good at finding
    # the biggest cluster.
    # bandwidth = cluster.estimate_bandwidth(all_cents, quantile=0.5)
    # I defined the good concentrating cluster to be within a circle of radius 50.
    bandwidth = 50
    clust = cluster.MeanShift(bandwidth=bandwidth, cluster_all=False)
    print(clust)
    # You'll see that MeanShift has high time complexity, O(T*n*log(n)),
    # T is the number of samples to fit with, here, T = n.
    t = time.perf_counter()
    clust.fit(all_cents)
    print(f"elapsed time: {time.perf_counter() - t}")

    fig, ax = plt.subplots()
    # select the leading colors
    colors = list(mcolors.BASE_COLORS.values())[:len(clust.cluster_centers_)]

    for k, (cluster_center, color) in enumerate(zip(clust.cluster_centers_, colors)):
        ax.scatter(all_cents[clust.labels_ == k, 0], all_cents[clust.labels_ == k, 1],
                   color=color, alpha=0.5)
        ax.scatter(*cluster_center, color="w", edgecolor=color)
    # noises
    ax.scatter(all_cents[clust.labels_ == -1, 0], all_cents[clust.labels_ == -1, 1],
               color=mcolors.CSS4_COLORS["dodgerblue"], alpha=0.5, label="noise")
    # centroid of all points
    ax.scatter(*get_center_of_group(all_cents), color="m", edgecolor="k", label="all center")

    count = Counter(clust.labels_)
    print(count)
    # label 0 is the biggest cluster
    ratio = count[0] / len(all_cents)
    dist = math.dist(get_center_of_group(all_cents), clust.cluster_centers_[0])
    print(f"{ratio:.2f} in the biggest cluster")
    print(f"{dist:.2f} far from the center of all points")
    plt.text(50, 50, f"ratio: {ratio:.2f}; dist: {dist:.2f}")

    ax.legend()

    # y-axis is flipped
    ax.set(xlim=(0, 640), ylim=(480, 0))
    ax.xaxis.set_ticks_position("top")

    plt.show()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise RuntimeError(f"\n\t usage: python {__file__} $(file_to_plot)")

    main(Path.cwd() / sys.argv[1])
