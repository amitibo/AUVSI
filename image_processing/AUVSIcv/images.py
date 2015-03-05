from __future__ import division
import exifread
from .utils import lla2ecef
import transformation_matrices as transforms
import numpy as np
import cv2
import json
import os


__all__ = [
    "Image",
]


def tagRatio(tag):
    ratio = tag.values[0].num/tag.values[0].den
    return ratio


def tagValue(tag):
    return tag.values[0]


class Image(object):
    def __init__(self, img_path):
        
        self._img = cv2.imread(img_path)
        data_path = os.path.splitext(img_path)[0]+'.txt'
        with open(data_path, 'r') as f:
            self._data = json.load(f)
            
        #
        # Get some data from the EXIF
        #
        with open(img_path, 'rb') as f:
            tags = exifread.process_file(f)

        #
        # Calculate camera matrix.
        #
        in_to_mm = 25.4
        FocalPlaneYResolution = tagRatio(tags['EXIF FocalPlaneYResolution'])
        FocalPlaneXResolution = tagRatio(tags['EXIF FocalPlaneXResolution'])
        ImageLength = tagValue(tags['EXIF ExifImageLength'])
        ImageWidth = tagValue(tags['EXIF ExifImageWidth'])
        FocalLength = tagRatio(tags['EXIF FocalLength'])
 
        f_x = FocalLength * FocalPlaneXResolution / in_to_mm
        f_y = FocalLength * FocalPlaneYResolution / in_to_mm
        self._K = np.array(((f_x, 0, ImageWidth/2), (0, f_y, ImageLength/2), (0, 0, 1)))        

        t = transforms.translation_matrix(
            lla2ecef(
                latitude=self._data['latitude'],
                longitude=self._data['longitude'],
                altitude=self._data['altitude']
            )
        )
        
        R = transforms.euler_matrix(
            ai=self._data['yaw'],
            aj=self._data['pitch'],
            ak=self._data['roll'],
            axes='sxyz'
        )
        
        self._Rt = np.dot(t, R)
        
    @property
    def img(self):
        return self._img
    
    @property
    def Rt(self):
        """Get the transform matrix of the camera.
        
        Returns the extrinsic parameters of the camera.
        """
        
        return self._Rt
    
    @property
    def K(self):
        """Get the K matrix of the camera.
        
        Retruns the intrinsic parameters of the camera.
        """
        
        return self._K