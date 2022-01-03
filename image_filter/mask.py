import cv2
import numpy as np
import numpy.ma as ma

def masked_mean(ndarray):
    sorted_arr = np.sort(ndarray, axis=None)
    # mask = np.ones(len(sorted_arr))
    # mask[:int(len(sorted_arr) * 0.9)] = 0
    # mx = ma.masked_array(sorted_arr, mask=mask)
    
    return sorted_arr[:int(len(sorted_arr) * 0.9)].mean()

def get_brightness(image, masking = False):
    """Returns the mean of brightness of an image.

    Arguments:
        image: The image to perform brightness calculation on.
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Value is as known as brightness.
    hue, saturation, value = cv2.split(hsv)  # can be gotten with hsv[:, :, 2] - the 3rd channel
    
    return round(masked_mean(value), 2) if masking else round(value.mean(), 2)
