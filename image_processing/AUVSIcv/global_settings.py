import numpy as np

IMAGE_RESIZE_RATIO = 0.25
IMAGE_RESIZE_MATRIX = np.array(((IMAGE_RESIZE_RATIO, 0, 0), (0, IMAGE_RESIZE_RATIO, 0), (0, 0, 1)))

#
# These values are used for blending targets into images.
# POISSON_INTENSITY_RATIO - Ratio by which to scale up the RGB values before applying possion noise.
# EMPIRICAL_IMAGE_INTENSITY - Some 'empirical' value that is supposed to be a normal intensity of an image.
#
EMPIRICAL_IMAGE_INTENSITY = 30
POISSON_INTENSITY_RATIO = 10