import numpy as np
from PIL import Image, ImageFilter


def Gaussian_Filter(arrF, radius):
    if radius <= 0:
        return arrF
    arrG = Image.fromarray((arrF * 255).astype(np.uint8)).convert(mode="L")

    output = arrG.filter(ImageFilter.GaussianBlur(radius=radius))
    output = np.array(output) / 255.0

    return np.clip(output, 0, 1)
