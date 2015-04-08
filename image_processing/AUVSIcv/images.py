from __future__ import division
import exifread
import transformation_matrices as transforms
import NED
from twisted.python import log
import global_settings as gs
import numpy as np
from datetime import datetime
import math
import cv2
import json
import os


__all__ = [
    "Image",
]

in_to_mm = 25.4

def tagRatio(tag):
    ratio = tag.values[0].num/tag.values[0].den
    return ratio


def tagValue(tag):
    return tag.values[0]


def overlay(img, overlay_img, overlay_alpha, M, center_patch=False):
    
    #
    # Calculate the destination pixels of the patch. This allows for much more efficient
    # copies (instead of copying a full 4000x3000 image).
    #
    offsets, dst_shape, shifts = calcDstLimits(img, overlay_img, M, center_patch)
    
    if dst_shape[0] == 0 or dst_shape[1]==0:
        #
        # Targets outside of the frame are not pasted.
        #
        return 
    
    T = np.eye(3)
    T[0, 2] = -offsets[0]
    T[1, 2] = -offsets[1]
    
    if center_patch:
        T1 = np.eye(3)
        T1[0, 2] = -shifts[0]
        T1[1, 2] = -shifts[1]

        T= np.dot(T, T1)
    
    flags = cv2.cv.CV_INTER_LINEAR+cv2.cv.CV_WARP_FILL_OUTLIERS
    overlay_img = cv2.warpPerspective(overlay_img, np.dot(T, M), dsize=dst_shape, flags=flags)
    overlay_alpha = cv2.warpPerspective(overlay_alpha, np.dot(T, M), dsize=dst_shape)
    
    #
    # Edge feather the alpha channel
    #
    ksize = 3
    ksigma = 0.3*((ksize-1)*0.5 - 1) + 0.8
    overlay_alpha = (overlay_alpha*cv2.GaussianBlur(cv2.erode(overlay_alpha, kernel=np.ones(shape=(ksize, ksize))), (ksize, ksize), ksigma))
    
    overlay_alpha = overlay_alpha[..., np.newaxis]
    
    #
    # Blend the image and overlay.
    #
    img[offsets[1]:offsets[1]+dst_shape[1], offsets[0]:offsets[0]+dst_shape[0], :3] = \
        (img[offsets[1]:offsets[1]+dst_shape[1], offsets[0]:offsets[0]+dst_shape[0], :3].astype(np.float32)*(1-overlay_alpha) + \
        overlay_img[..., :3].astype(np.float32)*overlay_alpha).astype(np.uint8)
        

def calcDstLimits(img, overlay_img, M, center_patch):
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
    if center_patch:
        x_shift = (dst_xlimit[1]+dst_xlimit[0] - isize[1])/2
        y_shift = (dst_ylimit[1]+dst_ylimit[0] - isize[0])/2
        
        dst_xlimit = [min(max(int(dst_xlimit[0]-x_shift), 0), isize[1]), min(max(int(dst_xlimit[1]-x_shift+1), 0), isize[1])]
        dst_ylimit = [min(max(int(dst_ylimit[0]-y_shift), 0), isize[0]), min(max(int(dst_ylimit[1]-y_shift+1), 0), isize[0])]
    else:
        x_shift, y_shift = 0, 0
        dst_xlimit = [min(max(int(dst_xlimit[0]), 0), img.shape[1]), min(max(int(dst_xlimit[1]+1), 0), img.shape[1])]
        dst_ylimit = [min(max(int(dst_ylimit[0]), 0), img.shape[0]), min(max(int(dst_ylimit[1]+1), 0), img.shape[0])]
              
    offsets = (dst_xlimit[0], dst_ylimit[0])
    shape = (dst_xlimit[1]-dst_xlimit[0], dst_ylimit[1]-dst_ylimit[0])
    
    return offsets, shape, (x_shift, y_shift)


class Image(object):
    def __init__(self, img_path, data_path=None, timestamp=None):
        
        #
        # Load image
        #
        self._path = img_path
        self._img = cv2.imread(img_path)
        
        #
        # Get the EXIF data
        #
        with open(img_path, 'rb') as f:
            self._tags = exifread.process_file(f)

        #
        # Load flight data
        #
        if data_path is not None:
            with open(data_path, 'rb') as f:
                self._flight_data = json.load(f)

            self._K = np.array(self._flight_data['K'])
        
            #
            # This is a hack to handle data_flight save in older
            # versions.
            #
            if not self._flight_data.has_key('resized_K'):
                self._K = np.dot(gs.IMAGE_RESIZE_MATRIX, self._K)
            
            self._datetime = self._flight_data['timestamp']
            
            #
            # Calculate extrinsic Matrix. The pitch and roll are ignored.
            #
            self.calculateExtrinsicMatrix(
                latitude=self._flight_data['lat']*1e-7,
                longitude=self._flight_data['lon']*1e-7,
                altitude=self._flight_data['relative_alt']*1e-3,
                yaw=math.degrees(self._flight_data['yaw']), 
                pitch=0,
                roll=0
            )
        else:
            #
            # Calculate the intrinsic data based on exif data if available.
            #
            self.calculateIntrinsicMatrix()            
            
        #
        # Get the time stamp.
        #
        if timestamp is not None:
            self._datetime = timestamp
        elif 'Image DateTime' in self._tags:            
            self._datetime = self._tags['Image DateTime'].values.replace(':', '_').replace(' ', '_') + datetime.now().strftime("_%f")
        else:
            log.msg('No Image DateTime tag using computer time.')
            self._datetime = datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")

        #
        # Some 'preprocessing'
        #
        self._limits = np.array(
            (
                (0, self.shape[1], self.shape[1], 0),
                (0, 0, self.shape[0], self.shape[0]),
                (1, 1, 1, 1.)
            )
        )
        self._Kinv = np.linalg.inv(self._K)
        
    def calculateIntrinsicMatrix(self):
        """Calculate camera intrinsic matrix
        
        Calculate the intrinsic matrix based on EXIF data.
        """

        if not 'EXIF FocalPlaneYResolution' in self._tags:
            log.msg("'EXIF FocalPlaneYResolution' missing, assuming default shape.")
            ImageLength, ImageWidth = self._img.shape[:2]
            self._K = np.array(((1, 0, ImageWidth/2), (0, 1, ImageLength/2), (0, 0, 1))) 
            return
        
        FocalPlaneYResolution = tagRatio(self._tags['EXIF FocalPlaneYResolution'])
        FocalPlaneXResolution = tagRatio(self._tags['EXIF FocalPlaneXResolution'])
        ImageLength = tagValue(self._tags['EXIF ExifImageLength'])
        ImageWidth = tagValue(self._tags['EXIF ExifImageWidth'])
        FocalLength = tagRatio(self._tags['EXIF FocalLength'])

        f_x = FocalLength * FocalPlaneXResolution / in_to_mm
        f_y = FocalLength * FocalPlaneYResolution / in_to_mm
        
        self._K = np.array(((f_x, 0, ImageWidth/2), (0, f_y, ImageLength/2), (0, 0, 1)))        
        log.msg("Setting the K matrix of the image to {K}.".format(K=self._K))

    def calculateExtrinsicMatrix(self, latitude, longitude, altitude, yaw, pitch, roll):
        """Calculate camera extrinsic matrix
        
        Calculate the extrinsic matrix in local cartesian mapping (NED) which
        is centered at the camera.
        """

        #
        # Calculate camera extrinsic matrix
        # Note:
        # 1) The local cartesian mapping (NED) is centered at the camera (therefore
        #    the translation matrix is an eye matrix).
        # 2) I need to add 90 degrees to make the coords correct, as X is
        #    pointing east and not north.
        #
        t = np.eye(4)
        R = transforms.euler_matrix(
            ai=math.radians(roll),
            aj=math.radians(pitch),
            ak=math.radians(yaw),
            axes='sxyz'
        )
        self._Rt = np.dot(t, R)

        self._latitude = latitude
        self._longitude = longitude
        self._altitude = altitude
        self._yaw = yaw
        self._pitch = pitch
        self._roll = roll
        
    def paste(self, target):
        """Draw a target on the image.

        This function uses the parameters of the target and the image to 
        calculate the location and then draw the target on the image.

        Parameters
        ----------
        target : Target object.
            Target to draw on the image, should be an object from a subclass of AUVSIcv BaseTarget.
        """

        #
        # Calculate the transform matrix from the target coordinates to the camera coordinates.
        # 
        target_H = target.H(
            latitude=self._latitude,
            longitude=self._longitude,
            altitude=self._altitude
        )            
        M1 = np.array(((1, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1)))
        M2 = np.eye(3, 4)
        M = np.dot(self.K, np.dot(M2, np.dot(np.linalg.inv(self.Rt), np.dot(target_H, M1))))

        overlay(img=self._img, overlay_img=target.img, overlay_alpha=target.alpha, M=M)

    def createPatches(self, patch_size, patch_shift, copy=True):
        """Create patches(crops) of an image
        
        This function crops patches of an image on a regulary spaced grid.
        
        Parameters
        ----------
        patch_size : int
            Scalar size (both width and height) of a rectangular patch.
        patch_shift : int
            Space (both horizontal and vertical) between patches.
        copy: Boolean
            Wheter to return a copy or a view into the original image.
        """
        
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
        """Paste a target on a patch
        
        The target is pasted in the center of the patch (the coords of the patch and target are ignored).
        
        Parameters
        ----------
        patch: array
            The patch on which the target is pasted into.
        target: target object.
            The target to paste on the patch.
        """

        target_H = target.H(
            latitude=self._latitude,
            longitude=self._longitude,
            altitude=self._altitude
        )            
        M1 = np.array(((1, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1)))
        M2 = np.eye(3, 4)
        M = np.dot(self.K, np.dot(M2, np.dot(np.linalg.inv(self.Rt), np.dot(target_H, M1))))

        overlay(img=patch, overlay_img=target.img, overlay_alpha=target.alpha, M=M, center_patch=True)
    
    def calculateQuad(self, ned):
        
        Ryaw = transforms.euler_matrix(0, 0, -np.deg2rad(self._yaw), axes='sxyz')
        x, y, h = ned.geodetic2ned([self._latitude, self._longitude, self._altitude])
        h = -h
        
        offset = np.array(
            (
                (y,),
                (x,),
                (h,)
            )
        )
        
        projections = offset + h * np.dot(np.array(((1., 0, 0), (0, 1, 0), (0, 0, -1.))), np.dot(Ryaw[:3, :3], np.dot(self._Kinv, self._limits)))
        
        return projections

    def coords2LatLon(self, x, y):
        
        
        Kinv = np.linalg.inv(self._K)
          
        point = np.array(
            (
                (x,),
                (y,),
                (1,)
            )
        )
        Ryaw = transforms.euler_matrix(0, 0, -np.deg2rad(self._yaw), axes='sxyz')
        ned = NED.NED(self._latitude, self._longitude, 0)
        x, y, h = ned.geodetic2ned([self._latitude, self._longitude, self._altitude])
        h = -h
        
        offset = np.array(
            (
                (y,),
                (x,),
                (h,)
            )
        )
        
        ned_coords = (offset + h * np.dot(np.array(((1., 0, 0), (0, 1, 0), (0, 0, -1.))), np.dot(Ryaw[:3, :3], np.dot(Kinv, point)))).flatten()
        
        lat, lon, alt = ned.ned2geodetic(ned=(ned_coords[1], ned_coords[0], ned_coords[2]))
        
        return lat, lon
    
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
    
    @property
    def datetime(self):
        """Get date time tag"""
        
        return self._datetime
    
    @property
    def path(self):
        """Get path of image"""
        
        return self._path

    @property
    def latitude(self):
        
        return self._latitude

    @property
    def longitude(self):
        
        return self._longitude

    @property
    def altitude(self):
        
        return self._altitude
    
    @property
    def shape(self):
        
        return self._img.shape