"""refer to https://pyimagesearch.com/2017/06/19/image-difference-with-opencv-and-python/"""

# TODO: how high the score needs to be to say they are similar?

import argparse

from skimage.metrics import structural_similarity
import cv2
import imutils
import numpy as np


class _ImageDiff:
    def compare(self, img1: np.ndarray, img2: np.ndarray) -> None:
        self._img1 = img1
        self._img2 = img2
        self._make_gray_images()
        self._compare_ssim()
        self._show_difference()
        self._show_threshold()
        self._show_contours()
        cv2.waitKey(0)

    def _make_gray_images(self) -> None:
        self._gray1 = cv2.cvtColor(self._img1, cv2.COLOR_BGR2GRAY)
        self._gray2 = cv2.cvtColor(self._img2, cv2.COLOR_BGR2GRAY)

    def _compare_ssim(self) -> None:
        score, self._diff = structural_similarity(
            self._gray1,
            self._gray2,
            data_range=255,
            full=True,
        )
        print("ssim: {}".format(score))

    def _show_difference(self) -> None:
        self._diff = (self._diff * 255).astype("uint8")
        cv2.imshow("diff", imutils.resize(self._diff, height=540))

    def _show_threshold(self) -> None:
        _, self._thresh, *_ = cv2.threshold(
            self._diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
        )
        cv2.imshow("thresh", imutils.resize(self._thresh, height=540))

    def _show_contours(self) -> None:
        cnts = cv2.findContours(
            self._thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        for c in imutils.grab_contours(cnts):
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(self._img1, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.rectangle(self._img2, (x, y), (x + w, y + h), (0, 0, 255), 2)
        cv2.imshow("original", imutils.resize(self._img1, height=540))
        cv2.imshow("modified", imutils.resize(self._img2, height=540))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--first", required=True, help="first input image")
    ap.add_argument("-s", "--second", required=True, help="second input image")
    args = ap.parse_args()

    img1 = cv2.imread(args.first)
    img2 = cv2.imread(args.second)

    _ImageDiff().compare(img1, img2)
