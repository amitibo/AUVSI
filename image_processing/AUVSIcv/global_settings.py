import numpy as np
import AUVSIcv
import os



#
# TARGET SIZE RANGES
#
NORMAL_TARGET_SIZE_RANGE = (0.6, 2.4)
QR_TARGET_SIZE_RANGE = (0.9, 1.2)

#
# Cv data base
#
AUVSI_CV_FOLDER = os.path.dirname(AUVSIcv.__file__)
SHAPE_DB_PATH = os.path.join(AUVSI_CV_FOLDER,
                             r'Contours\Shapes\Contour_DB.npy')
Shape_Name_DB_Path = os.path.join(AUVSI_CV_FOLDER,
                                  r'Contours\Shapes\Contour_Name_DB.npy')
Letter_DB_Path = os.path.join(AUVSI_CV_FOLDER,
                              r'Contours\Letters\Contour_DB.npy')
Letter_Name_DB_Path = os.path.join(AUVSI_CV_FOLDER,
                                   r'Contours\Letters\Contour_Name_DB.npy')


#
# These values are used for blending targets into images.
# POISSON_INTENSITY_RATIO - Ratio by which to scale up the RGB values before applying possion noise.
# EMPIRICAL_IMAGE_INTENSITY - Some 'empirical' value that is supposed to be a normal intensity of an image.
#
EMPIRICAL_IMAGE_INTENSITY = 30
POISSON_INTENSITY_RATIO = 10