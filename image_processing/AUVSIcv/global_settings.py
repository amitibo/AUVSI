import numpy as np

IMAGE_RESIZE_RATIO = 0.25
IMAGE_RESIZE_MATRIX = np.array(((IMAGE_RESIZE_RATIO, 0, 0), (0, IMAGE_RESIZE_RATIO, 0), (0, 0, 1)))

#
# TARGET SIZE RANGES
#
NORMAL_TARGET_SIZE_RANGE = (0.6, 2.4)
QR_TARGET_SIZE_RANGE = (0.9, 1.2)

#
# These values are used for blending targets into images.
# POISSON_INTENSITY_RATIO - Ratio by which to scale up the RGB values before applying possion noise.
# EMPIRICAL_IMAGE_INTENSITY - Some 'empirical' value that is supposed to be a normal intensity of an image.
#
EMPIRICAL_IMAGE_INTENSITY = 30
POISSON_INTENSITY_RATIO = 10