from typing import Dict, Tuple

from nptyping import Int32, NDArray
from numpy import array


# Define a dictionary to store the min and max weights of each color (hsv).
# {color: (array[hmin, smin, vmin], array(hmax, smax, vmax))}
COLOR_DICT: Dict[str, Tuple[NDArray[(3,), Int32], NDArray[(3,), Int32]]] = {
    "black": (array([0, 0, 0]), array([180, 255, 46])),
    "blue": (array([100, 43, 46]), array([124, 255, 255])),
    "cyan": (array([78, 43, 46]), array([99, 255, 255])),
    "dark red": (array([0, 43, 46]), array([10, 255, 255])),
    "gray": (array([0, 0, 46]), array([180, 43, 220])),
    "green": (array([35, 43, 46]), array([77, 255, 255])),
    "light red": (array([156, 43, 46]), array([180, 255, 255])),
    "orange": (array([11, 43, 46]), array([25, 255, 255])),
    "purple": (array([125, 43, 46]), array([155, 255, 255])),
    "white": (array([0, 0, 221]), array([180, 30, 255])),
    "yellow": (array([26, 43, 46]), array([34, 255, 255])),
}
