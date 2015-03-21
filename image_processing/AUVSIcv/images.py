from __future__ import division
import exifread
import transformation_matrices as transforms
import numpy as np
import math
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


def calcDstLimits(img, overlay_img, M):
    """Calculate the limits of the overlay in the destination image."""

    osize = overlay_img.shape[:2]
    isize = img.shape[:2]
    
    limits = np.float32((((0, 0), (0, osize[0]), osize[::-1], (osize[1], 0)),))

    limits_trans = cv2.perspectiveTransform(limits, M)
    dst_xlimit = cv2.minMaxLoc(limits_trans[0, :, 0])[:2]
    dst_ylimit = cv2.minMaxLoc(limits_trans[0, :, 1])[:2]

    dst_xlimit = [min(max(int(dst_xlimit[0]), 0), img.shape[1]), min(max(int(dst_xlimit[1]+1), 0), img.shape[1])]
    dst_ylimit = [min(max(int(dst_ylimit[0]), 0), img.shape[0]), min(max(int(dst_ylimit[1]+1), 0), img.shape[0])]
    
    offsets = (dst_xlimit[0], dst_ylimit[0])
    shape = (dst_xlimit[1]-dst_xlimit[0], dst_ylimit[1]-dst_ylimit[0])
    
    return offsets, shape


def overlay(img, overlay_img, overlay_alpha, M):
    
    #
    # Calculate the destination pixels of the patch. This allows for much more efficient
    # copies (instead of copying a full 4000x3000 image).
    #
    offsets, dst_shape = calcDstLimits(img, overlay_img, M)
    
    if dst_shape[0] == 0 or dst_shape[1]==0:
        #
        # Targets outside of the frame are not pasted.
        #
        return 
    
    T = np.eye(3)
    T[0, 2] = -offsets[0]
    T[1, 2] = -offsets[1]
    
    overlay_img = cv2.warpPerspective(overlay_img, np.dot(T, M), dsize=dst_shape)
    overlay_alpha = cv2.warpPerspective(overlay_alpha, np.dot(T, M), dsize=dst_shape)[..., np.newaxis]

    img[offsets[1]:offsets[1]+dst_shape[1], offsets[0]:offsets[0]+dst_shape[0], :3] = \
        (img[offsets[1]:offsets[1]+dst_shape[1], offsets[0]:offsets[0]+dst_shape[0], :3].astype(np.float32)*(1-overlay_alpha) + \
        overlay_img[..., :3].astype(np.float32)*overlay_alpha).astype(np.uint8)
        

def calcDstPatchLimits(img, overlay_img, M):
    """Calculate the limits of the overlay in the destination image."""

    osize = overlay_img.shape[:2]
    isize = img.shape[:2]
    
    limits = np.float32((((0, 0), (0, osize[0]), osize[::-1], (osize[1], 0)),))

    limits_trans = cv2.perspectiveTransform(limits, M)
    dst_xlimit = cv2.minMaxLoc(limits_trans[0, :, 0])[:2]
    dst_ylimit = cv2.minMaxLoc(limits_trans[0, :, 1])[:2]

    #
    # Center the patch
    #
    x_shift = (dst_xlimit[1]+dst_xlimit[0] - isize[1])/2
    y_shift = (dst_ylimit[1]+dst_ylimit[0] - isize[0])/2
    
    dst_xlimit = [min(max(int(dst_xlimit[0]-x_shift), 0), isize[1]), min(max(int(dst_xlimit[1]-x_shift+1), 0), isize[1])]
    dst_ylimit = [min(max(int(dst_ylimit[0]-y_shift), 0), isize[0]), min(max(int(dst_ylimit[1]-y_shift+1), 0), isize[0])]
    
    offsets = (dst_xlimit[0], dst_ylimit[0])
    shape = (dst_xlimit[1]-dst_xlimit[0], dst_ylimit[1]-dst_ylimit[0])
    
    return offsets, shape, (x_shift, y_shift)


def overlayPatch(img, overlay_img, overlay_alpha, M):
    
    offsets, dst_shape, shifts = calcDstPatchLimits(img, overlay_img, M)
    
    T2 = np.eye(3)
    T2[0, 2] = -shifts[0]
    T2[1, 2] = -shifts[1]

    T1 = np.eye(3)
    T1[0, 2] = -offsets[0]
    T1[1, 2] = -offsets[1]
    
    overlay_img = cv2.warpPerspective(overlay_img, np.dot(T1, np.dot(T2, M)), dsize=dst_shape)
    overlay_alpha = cv2.warpPerspective(overlay_alpha, np.dot(T1, np.dot(T2, M)), dsize=dst_shape)[..., np.newaxis]

    img[offsets[1]:offsets[1]+dst_shape[1], offsets[0]:offsets[0]+dst_shape[0], :3] = \
        (img[offsets[1]:offsets[1]+dst_shape[1], offsets[0]:offsets[0]+dst_shape[0], :3].astype(np.float32)*(1-overlay_alpha) + \
        overlay_img[..., :3].astype(np.float32)*overlay_alpha).astype(np.uint8)
        

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
        # Calculate camera intrinsic matrix.
        #
        # in_to_mm = 25.4
        # FocalPlaneYResolution = tagRatio(tags['EXIF FocalPlaneYResolution'])
        # FocalPlaneXResolution = tagRatio(tags['EXIF FocalPlaneXResolution'])
        # ImageLength = tagValue(tags['EXIF ExifImageLength'])
        # ImageWidth = tagValue(tags['EXIF ExifImageWidth'])
        # FocalLength = tagRatio(tags['EXIF FocalLength'])

        #TODO remove mock values and use real values
        in_to_mm = 25.4
        FocalPlaneYResolution = 1
        FocalPlaneXResolution = 1
        ImageLength = 1
        ImageWidth = 1
        FocalLength = 1
 
        f_x = FocalLength * FocalPlaneXResolution / in_to_mm
        f_y = FocalLength * FocalPlaneYResolution / in_to_mm
        self._K = np.array(((f_x, 0, ImageWidth/2), (0, f_y, ImageLength/2), (0, 0, 1)))        

        #
        # Calculate camera extrinsic matrix
        # Note:
        # 1) The local cartesian mapping (NED) is centered at the camera.
        # 2) For some reason, I need to add 90 degrees to make the coords
        # correct.
        t = np.eye(4)
        R = transforms.euler_matrix(
            ai=math.radians(self._data['yaw']),
            aj=math.radians(self._data['pitch']),
            ak=math.radians(self._data['roll']+90),
            axes='sxyz'
        )
        
        self._Rt = np.dot(t, R)
        
    def paste(self, target):
        """Draw a target on the image.

        This function uses the parameters of the target and the image to 
        calculate the location and then draw the target on the image.

        Parameters
        ----------
        target : Target object.
            Target to draw on the image, should be an object from a subclass of
            AUVSIcv BaseTarget.
        """

        #
        # Calculate the transform matrix from the target coordinates to the camera coordinates.
        # 
        target_H = target.H(
            latitude=self._data['latitude'],
            longitude=self._data['longitude'],
            altitude=self._data['altitude']
        )            
        M1 = np.array(((1, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1)))
        M2 = np.eye(3, 4)
        M = np.dot(self.K, np.dot(M2, np.dot(np.linalg.inv(self.Rt), np.dot(target_H, M1))))

        overlay(img=self._img, overlay_img=target.img, overlay_alpha=target.alpha, M=M)

    def createPatches(self, patch_size, patch_shift, copy=True):
        """Create patches(crops) of an image"""
        
        patch_height, patch_width = patch_size
        nx = int((self._img.shape[1] - patch_width)/patch_shift)
        ny = int((self._img.shape[0] - patch_height)/patch_shift)
        
        for i in range(nx):
            for j in range(ny):
                sx = i*patch_shift
                sy = j*patch_shift
                patch = self._img[sy:sy+patch_height, sx:sx+patch_width, :]
                yield patch.copy()

    def pastePatch(self, patch, target):
        """Paste a target on a patch"""

        target_H = target.H(
            latitude=self._data['latitude'],
            longitude=self._data['longitude'],
            altitude=self._data['altitude']
        )            
        M1 = np.array(((1, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1)))
        M2 = np.eye(3, 4)
        M = np.dot(self.K, np.dot(M2, np.dot(np.linalg.inv(self.Rt), np.dot(target_H, M1))))

        overlayPatch(img=patch, overlay_img=target.img, overlay_alpha=target.alpha, M=M)
    
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