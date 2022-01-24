import timeit

import cv2
import numpy as np

from util.path import to_abs_path


# assume the face area
fx, fy, fw, fh = 185, 137, 215, 215
*_, value = cv2.split(
    cv2.cvtColor(
        cv2.imread(
            to_abs_path("image_filter/img/ref_img.jpg")
        ), cv2.COLOR_BGR2HSV
    )
)


def loop_over():
    val = value.astype(np.float32)
    for y in range(len(val)):
        for x in range(len(val[0])):
            if y >= fy and y <= fy+fh and x >= fx and x <= fx+fw:
                # face area
                val[y][x] *= 2
            else:
                val[y][x] *= 0.5
    return val


def mask_and_slice():
    val = value.astype(np.float32)
    face_area = np.zeros(val.shape, dtype=np.bool8)
    face_area[fy:fy+fh+1, fx:fx+fw+1] = 1
    val[face_area] *= 2
    val[~face_area] *= 0.5
    return val


def test_speed():
    # make sure they're the same
    assert np.array_equal(loop_over(), mask_and_slice())
    loop_time = timeit.timeit(loop_over, number=100)
    mask_time = timeit.timeit(mask_and_slice, number=100)
    print(f"loop: {loop_time}")
    print(f"mask: {mask_time}")
    print(f"slow factor: {round(loop_time/mask_time, 2)}")


if __name__ == "__main__":
    test_speed()
