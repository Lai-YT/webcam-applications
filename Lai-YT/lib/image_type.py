"""Pre-defined type aliases of numpy image"""

from nptyping import NDArray, UInt8
from typing import Any

# A colored image has 3 dimensions. The third dimension is 3 (color channels).
# Gray image has 2 dimensions.
# Ther integer types are both numpy.uint8

ColorImage = NDArray[(Any, Any, 3), UInt8]
GrayImage  = NDArray[(Any, Any), UInt8]
