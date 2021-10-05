import numpy as np


def getColorList():

    dict = {
        "black":     (np.array([0, 0, 0]),     np.array([180, 255, 46])),
        "gray":      (np.array([0, 0, 46]),    np.array([180, 43, 220])),
        "white":     (np.array([0, 0, 221]),   np.array([180, 30, 255])),
        "light red": (np.array([156, 43, 46]), np.array([180, 255, 255])),
        "dark red":  (np.array([0, 43, 46]),   np.array([10, 255, 255])),
        "orange":    (np.array([11, 43, 46]),  np.array([25, 255, 255])),
        "yellow":    (np.array([26, 43, 46]),  np.array([34, 255, 255])),
        "green":     (np.array([35, 43, 46]),  np.array([77, 255, 255])),
        "cyan":      (np.array([78, 43, 46]),  np.array([99, 255, 255])),
        "blue":      (np.array([100, 43, 46]), np.array([124, 255, 255])),
        "purple":    (np.array([125, 43, 46]), np.array([155, 255, 255]))
    }

    return dict


if __name__ == '__main__':
    color_dict = getColorList()
    print(color_dict)

    num = len(color_dict)
    print('num=', num)

    for d in color_dict:
        print('key=', d)
        print('value=', color_dict[d][1])