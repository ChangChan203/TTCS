import numpy as np
import scipy.ndimage as img


def lp(matX, p):
    return np.power(np.sum(np.power(np.abs(matX), p), axis=0), 1 / p)


def SquareEye_Effect(arrF, vecC, sigma, p):
    vecC = np.array(vecC).reshape(-1, 1)
    m, n = arrF.shape
    u, v = np.meshgrid(np.arange(n), np.arange(m))

    matX = np.vstack((v.flatten(), u.flatten())).astype(float)
    matR = vecC - matX
    matX += matR * np.exp(-lp(matR, p) ** 2 / (2 * sigma ** 2))

    arrG = img.map_coordinates(arrF, matX)
    arrG = arrG.reshape(m,n)

    return np.clip(arrG, 0, 1)
