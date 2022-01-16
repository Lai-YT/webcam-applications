import cv2
import dlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma

from imutils import face_utils
from nptyping import NDArray
from numpy.ma.core import MaskedConstant

from util.image_type import ColorImage

np.set_printoptions(threshold=np.inf)
class ImageFilter:
    """Handle processes which filter the brightness of the image."""

    _face_detector: dlib.fhog_object_detector = dlib.get_frontal_face_detector()

    def __init__(self) -> None:
        self._image = None
        self._faces = None
        self._brightness = 0

    def refresh_image(self, image: ColorImage) -> None:
        """Refreshes the image in the filter and starts the process of filtering."""
        self._image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        # start process
        self._detect_face()
        self._get_brightness()

    def plot_image(self) -> None:
        """Plot the image and show filtered brightness on the window."""
        title = f"Brightness: {self._brightness}"

        plt.imshow(self._image)
        plt.title(title)
        plt.show()

    def _detect_face(self) -> None:
        """Detects face in a image and stores data of the face."""
        self._faces: dlib.rectangles = self._face_detector(self._image)

    def _get_brightness(self) -> None:
        """Returns the filtered mean of brightness of an image."""
        hsv = cv2.cvtColor(self._image, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel

        mask = self._generate_mask(value)
        # array of "value" channel with face area masked
        masked_value = self._mask_face_area(value, mask)
        self._brightness = round(100 * self._filtered_mean(masked_value) / 255, 2)

    def _generate_mask(self, ndarray: NDArray) -> NDArray:
        """Get the boundaries of face area and generate the array with
        corresponding elements masked.
        
        Note: 
            The size of the mask should be the same as "one" channel of an image,
        passing the size of self._image leads to size error because its size is three
        times larger than the "value" channel of hsv. 
        """
        # doesn't handle multiple faces
        if len(self._faces) == 1:
            fx, fy, fw, fh = face_utils.rect_to_bb(self._faces[0])
            cv2.rectangle(self._image, (fx, fy), (fx+fw, fy+fh), (255, 0, 255), 1)
        # generate mask with face area masked
        mask = np.zeros(ndarray.shape)
        for i in range(fy, fy+fh+1):
            for j in range(fx, fx+fx+1):
                mask[i][j] = 1
        return mask

    def _mask_face_area(self, ndarray: NDArray, mask: NDArray) -> NDArray:
        return ma.masked_array(ndarray, mask)

    @staticmethod
    def _filtered_mean(ndarray: NDArray) -> float:
        """Filter out the brightest and darkest 5% area of a masked image."""
        # Flatten the array to 1D and sort it in increasing order.
        sorted_arr = np.sort(ndarray, axis=None)
        # Cut the masked value to fix the size of the masked array.
        arr = []
        for element in sorted_arr:
            if type(element) != MaskedConstant:
                arr.append(element)
        # Convert the array to ndarray to use the mean method.
        arr = np.array(arr)
        return arr[int(arr.size * 0.05):int(arr.size * 0.95)].mean()
