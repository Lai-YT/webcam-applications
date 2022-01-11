import cv2
import dlib
import matplotlib.pyplot as plt
import numpy as np
import numpy.ma as ma
from imutils import face_utils
from nptyping import NDArray

from util.image_type import ColorImage


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
        self._mask_face_area()
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

    def _mask_face_area(self) -> None:
        # doesn't handle multiple faces
        if len(self._faces) == 1:
            fx, fy, fw, fh = face_utils.rect_to_bb(self._faces[0])

    def _get_brightness(self) -> None:
        """Returns the mean of brightness of an image.

        Arguments:
            image: The image to perform brightness calculation on.
            mask:  If mask is True, the brightest 10% area of the image
                   will be filtered.
        """
        hsv = cv2.cvtColor(self._image, cv2.COLOR_BGR2HSV)
        # Value is as known as brightness.
        hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
        self._brightness = round(100 * self._filtered_mean(value) / 255, 2)

    @staticmethod
    def _filtered_mean(ndarray: NDArray) -> float:
        sorted_arr = np.sort(ndarray, axis=None)
        return sorted_arr[:int(len(sorted_arr) * 0.9)].mean()
