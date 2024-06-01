import numpy as np


def MeanFilterRec(arrF, m):
    f = np.pad(arrF, ((0, 0), (m, m)))
    f1 = np.roll(f, m // 2 + 1, axis=1)
    f2 = np.roll(f, -m // 2 + 1, axis=1)
    g = np.cumsum((-f1 + f2), axis=1)
    return g[:, m:-m] / m


def Mean_Filter(arrF, size):
    if size <= 0:
        return arrF

    arrG = MeanFilterRec(arrF, int(size)).T
    arrG = MeanFilterRec(arrG, int(size)).T

    return np.clip(arrG, 0, 1)
