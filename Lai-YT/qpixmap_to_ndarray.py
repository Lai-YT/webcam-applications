import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication


def take_screenshot() -> "QPixmap":
    app = QApplication([])
    # Have a QScreen instance to grabWindow with.
    screen = QApplication.primaryScreen()
    screenshot = screen.grabWindow(QApplication.desktop().winId())

    return screenshot


def qpixmap_to_ndarray(image: "QPixmap") -> "NDArray[(Any, Any, 3), UInt8]":
    qimage = image.toImage()
    
    width = qimage.width()
    height = qimage.height()

    byte_str = qimage.constBits().asstring(height * width * 4)
    ndarray = np.frombuffer(byte_str, np.uint8).reshape((height, width, 4))

    return ndarray

def get_dominant_color(image, k=4, image_processing_size = None):
    """
    takes an image as input
    returns the dominant color of the image as a list
    
    dominant color is found by running k means on the 
    pixels & returning the centroid of the largest cluster

    processing time is sped up by working with a smaller image; 
    this resizing can be done with the image_processing_size param 
    which takes a tuple of image dims as input

    >>> get_dominant_color(my_image, k=4, image_processing_size = (25, 25))
    [56.2423442, 34.0834233, 70.1234123]
    """
    #resize image if new dims provided
    if image_processing_size is not None:
        image = cv2.resize(image, image_processing_size, 
                            interpolation = cv2.INTER_AREA)
    
    #reshape the image to be a list of pixels
    image = image.reshape((image.shape[0] * image.shape[1], 3))

    #cluster and assign labels to the pixels 
    clt = KMeans(n_clusters = k)
    labels = clt.fit_predict(image)

    #count labels to find most popular
    label_counts = Counter(labels)

    #subset out most popular centroid
    dominant_color = clt.cluster_centers_[label_counts.most_common(1)[0][0]]

    return list(dominant_color)

if __name__ == "__main__":
    screenshot = cv2.resize(qpixmap_to_ndarray(take_screenshot()), (1440, 810))
    cv2.imshow("screenshot", screenshot)
    cv2.waitKey(0)
