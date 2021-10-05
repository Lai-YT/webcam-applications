import cv2

import lib.color_lib as color_lib


class DominantColorDetector:
    """Find the dominant color and its colorfulness of an image."""
    def get_dominant_color(frame) -> str:
        """Return the dominant color of the image."""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        maxsum = -100
        color = None
        color_dict = color_lib.getColorList()

        for d in color_dict:
            mask = cv2.inRange(hsv, color_dict[d][0], color_dict[d][1])
            binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)[1]
            binary = cv2.dilate(binary, None, iterations=2)
            cnts = cv2.findContours(binary.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]
            sum = 0
            for c in cnts:
                sum += cv2.contourArea(c)
        if sum > maxsum :
            maxsum = sum
            color = d

        print(color)
        return color

    def get_colorfulness(color: str):
        """Return the colorfulness of the dominant color"""
        light_color = {"white", "light red", "orange", "yellow", "cyan"}
        colorfulness = ""

        if color in light_color:
            colorfulness = "light color"
        else:
            colorfulness = "dark color"

        print(colorfulness)
        return colorfulness
