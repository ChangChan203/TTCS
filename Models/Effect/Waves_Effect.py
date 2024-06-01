import numpy as np
import scipy.ndimage as img


def Waves_Effect(arrF, ampl, fre, phase):
    m, n = arrF.shape
    u, v = np.meshgrid(np.arange(n + ampl[1] * 2),
                       np.arange(m + ampl[0] * 2))
    matX = np.stack((v, u)).astype(float)

    a = ampl[0] * np.sin(matX[0] / fre[1] + phase[0])
    matX[0] += a - ampl[0]

    b = ampl[1] * np.sin(matX[0] / fre[1] + phase[1])
    matX[1] += b - ampl[1]

    arrG = img.map_coordinates(arrF, matX)
    arrG = arrG.reshape(matX.shape[1], matX.shape[2])

    return np.clip(arrG, 0, 1)
