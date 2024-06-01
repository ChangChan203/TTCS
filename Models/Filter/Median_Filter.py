import numpy as np
from scipy.ndimage import median_filter


def Median_Filter(arrF, size):
    if size <= 0:
        return arrF
    size = int((size // 2) * 2) + 1

    output = median_filter(arrF, size)

    return np.clip(output, 0, 1)
