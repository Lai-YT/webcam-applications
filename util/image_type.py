"""Pre-defined type aliases of numpy image"""

from typing import Any

from nptyping import NDArray, UInt8

# A colored image has 3 dimensions. The third dimension is 3 (color channels).
# Gray image has 2 dimensions.
# Their integer types are both numpy.uint8
#
# The actual type under "nptyping" is as the comments behind.
# I'm not using that because they are not compatible with cv2,
# and VS Code shows the type as "Shape" instead of the shape of array.

ColorImage = NDArray[Any, UInt8]  # NDArray[Shape["*, *, 3"], UInt8]
GrayImage = NDArray[Any, UInt8]  # NDArray[Shape["*, *"], UInt8]
