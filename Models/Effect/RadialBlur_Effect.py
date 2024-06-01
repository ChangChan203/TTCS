import numpy as np
import scipy.ndimage as img


def to_r(f, m, n, rmax, pmax):
    rs, phis = np.meshgrid(np.linspace(0, rmax, n),
                           np.linspace(0, pmax, m), sparse=True)

    xs, ys = rs * np.cos(phis), rs * np.sin(phis)
    xs, ys = xs.reshape(-1), ys.reshape(-1)

    coord = np.vstack((ys, xs))

    vecC = np.array([f.shape[0] // 2, f.shape[1] // 2]).reshape(2, 1)
    coord += vecC

    g = img.map_coordinates(f, coord, order=3)
    g = g.reshape(m, n)

    return np.flipud(g)


def from_r(g, m, n, rmax, pmax):
    xs, ys = np.meshgrid(np.arange(n), np.arange(m), sparse=True)

    xs -= n // 2
    ys -= m // 2

    rs, phis = np.sqrt(xs ** 2 + ys ** 2), np.arctan2(ys, xs)
    phis += np.pi

    rs, phis = rs.reshape(-1), phis.reshape(-1)

    iis = phis / pmax * (m - 1)
    jjs = rs / rmax * (n - 1)
    coord = np.vstack((iis, jjs))

    h = img.map_coordinates(g, coord, order=3)
    h = h.reshape(m, n)

    return np.fliplr(np.flipud(h))


def RadialBlur_Effect(arrF, sigma):
    arrF = np.flipud(arrF)
    m, n = arrF.shape

    rmax = np.sqrt((m / 2) ** 2 + (n / 2) ** 2)
    pmax = 2 * np.pi

    arrG = to_r(arrF, m, n, rmax, pmax)
    blurred_arrG = img.gaussian_filter1d(arrG, sigma=sigma, axis=0, mode="wrap")

    arrH = from_r(blurred_arrG, m, n, rmax, pmax)

    return np.clip(arrH, 0, 1)
