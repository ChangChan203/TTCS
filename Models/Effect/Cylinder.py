import numpy as np
import scipy.ndimage as img


def Cylinder(arrF, angle_shift):
    m, n = arrF.shape
    u, v = np.meshgrid(np.arange(n), np.arange(m))
    matX = np.stack((v, u)).astype(float)

    vecC = np.array([arrF.shape[0] // 2, arrF.shape[1] // 2]).reshape(2, 1, 1)
    diff = matX - vecC

    r = np.linalg.norm(diff, axis=0)
    y = (r / (arrF.shape[0] // 2)) * (arrF.shape[0] - 1)

    angle = np.arctan2(diff[0], diff[1])
    angle -= angle.min()
    angle /= angle.max()
    angle = (angle + angle_shift / 360.0) % 1.0
    x = angle * (arrF.shape[1] - 1)

    matX = np.stack([y, x])

    arrG = img.map_coordinates(np.flipud(arrF), matX)
    arrG = arrG.reshape(m, n)

    return np.clip(arrG, 0, 1)
