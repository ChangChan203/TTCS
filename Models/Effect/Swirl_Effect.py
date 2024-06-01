import numpy as np
import scipy.ndimage as img


def Swirl_Effect(arrF, vecC, sigma, mag):
    m, n = arrF.shape
    u, v = np.meshgrid(np.arange(n), np.arange(m))
    matX = np.stack((v, u)).astype(float)

    vecC = np.asarray(vecC).reshape(2, 1, 1)
    diff = matX - vecC
    r = np.linalg.norm(diff, axis=0)
    angle = np.arctan2(diff[1], diff[0])

    dist = r / r.max()
    gaussian = np.exp(-dist ** 2 / (2 * (sigma ** 2)))

    angle += mag * gaussian

    matX = np.stack([r * np.cos(angle), r * np.sin(angle)])
    matX += vecC

    arrG = img.map_coordinates(arrF, matX)
    arrG = arrG.reshape(m, n)

    return np.clip(arrG, 0, 1)
