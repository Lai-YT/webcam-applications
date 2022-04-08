# Face centroid

We try to track the movement of the user. \
When the users are concentrating, usually their faces stick to a certain area. \
So by plotting the centroid point of faces (nose) and calculating how dense they are, we're able to tell how concentrating the user may be. \

## Implementation

We use *MeanShift* with *bandwidth* 50 to get the possible clusters. \
The reason why 50 is chosen is because we define the *proper concentrating area* to be a circle with radius 50. \
After the clustering, we get several clusters.

1. We take the cluster with the most face centroid points and calculate the ratio over all points. \
For example, if there are 1,000 centroid points and 600 of them are in the biggest cluster, them the ratio is 0.6. \
The larger the ratio (<= 1.0) is, the denser the points are, and so the more concentrating the user may be.
2. We calculate the distance between the center of that biggest cluster and the center of all points. \
The shorter the distance is, the denser the points are, and so the more concentrating the user may be.

The 2 numbers calculated above, ratio and distance, are the indices we used to indicate how concentrating the user may be.

<img src="./concentration-with-face-centroid.png" alt="clusters and centers" width="750" height="380">
