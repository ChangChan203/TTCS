import numpy as np
import scipy.ndimage as img


def delta(r, sigma):
    return np.where(r < sigma, 1 - r / sigma, 0)


def FishEye_Effect(arrF, vecC, sigma=100, dfct=delta):
    vecC = np.array(vecC).reshape(-1, 1)
    m, n = arrF.shape
    u, v = np.meshgrid(np.arange(n), np.arange(m))

    matX = np.vstack((v.flatten(), u.flatten())).astype(float)
    matR = vecC - matX

    dist = np.sqrt(np.sum(matR ** 2, axis=0))
    matX = matX + matR * dfct(dist, sigma)

    arrG = img.map_coordinates(arrF, matX)
    arrG = arrG.reshape(m, n)

    return np.clip(arrG, 0, 1)
