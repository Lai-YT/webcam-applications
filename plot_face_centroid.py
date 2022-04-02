from ast import literal_eval as make_tuple
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def get_centroid_of_group(points):
    x = [p[0] for p in points]
    y = [p[1] for p in points]
    l = len(points)
    return (np.sum(x) / l, np.sum(y) / l)


target = Path(__file__).parent / "face_centroid.log"

# "all" keeps the order
centroids = {"hog": [], "mtcnn": [], "all": []}
with target.open("r") as f:
    for line in f:
        line = line.rstrip("\n")
        cat, centroid = line.split(" ", 1)
        centroid = make_tuple(centroid)
        centroids[cat].append(centroid)
        centroids["all"].append(centroid)

print(f"number of faces: {len(centroids['all'])}")

fig, ax = plt.subplots()

# centroids of face
ax.scatter([c[0] for c in centroids["hog"]], [c[1] for c in centroids["hog"]], color="b", alpha=0.3, label="hog")
ax.scatter([c[0] for c in centroids["mtcnn"]], [c[1] for c in centroids["mtcnn"]], color="r", alpha=0.3, label="mtcnn")

# centroids of group
ax.scatter(*get_centroid_of_group(centroids["hog"]), color="b", facecolor="white", label="hog centroid")
ax.scatter(*get_centroid_of_group(centroids["mtcnn"]), color="r", facecolor="white", label="mtcnn centroid")
ax.scatter(*get_centroid_of_group(centroids["all"]), color="m", facecolor="white", label="all centroid")

ax.legend()

# y-axis is flipped
ax.set(xlim=(0, 640), ylim=(480, 0))
ax.xaxis.set_ticks_position("top")

plt.show()
