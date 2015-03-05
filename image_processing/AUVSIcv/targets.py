from __future__ import division
import numpy as np
import transformation_matrices as transforms
import aggdraw
import Image
from .utils import lla2ecef
import cv2


__all__ = [
    "CircleTarget",
]


class BaseTarget(object):
    """
    Base target from which all other target inherit.
    
    size: float
        Size of target in meters.
    orientation: float
        Orientation of the target(degrees) in respect to the north.
    altitude: float
        Altitude of the target in meters
    longitude: float
        Longitude coord of the target
    latitude: float
        Latitude coord of the target
    color: three tuple
        Color of the target
    letter: char
        Letter to be drawn in the center of the target
    font_color: three tuple
        Color of the letter
    font_size: float
        Size of the letter, ratio to full target size.
    font: string
        Path of font to use
    template_size: int, optional(=400)
        Size of base template target (before pasting into drone image)
    """
    
    def __init__(
        self,
        size,
        orientation,
        altitude,
        longitude,
        latitude,
        color,
        letter,
        font_color,
        font_size=200,
        font=r"C:\Windows\Fonts\Arialbd.ttf",
        template_size=400
        ):
        
        self._size = size
        self._orientation = orientation
        self._altitude = altitude
        self._longitude = longitude
        self._latitude = latitude
        self._color = color
        self._letter = letter
        self._font_color = font_color
        self._font_size = font_size
        self._font = font
        self._template_size = template_size
        
        self._drawTemplate()
        self._calcTransform()
        
    def _calcTransform(self):
        """Calculate the transform matrix of the target."""
        
        T = transforms.translation_matrix(lla2ecef(self._latitude, self._longitude, self._altitude))
        R = transforms.euler_matrix(self._orientation, 0, 0, 'szxy')
        S = transforms.scale_matrix(self._size/self._template_size)
        
        self._H = np.dot(T, np.dot(R, S))

    def _drawForm(self, ctx, brush):
        """Draw the form of the target"""
    
        raise NotImplementedError()
    
    def _drawLetter(self, ctx):
        """Draw the letter on the target.

        This function is called after the target has been drawn.

        Parameters
        ----------
        ctx: aggdraw context
            The context to drawon.
        """
        
        font = aggdraw.Font(self._font_color, self._font, self._font_size)
        text_size = ctx.textsize(self._letter, font)
        position = [self._template_size/2-text_size[i]/2 for i in range(2)]
        ctx.text(position, self._letter, font)    

    def _drawTemplate(self):
        """Draw the target on the base template"""

        img = Image.new(
            mode='RGBA',
            size=(self._template_size, self._template_size),
            color=(0, 0, 0, 0)
        )
        ctx = aggdraw.Draw(img)
        brush = aggdraw.Brush(self._color, 255)
    
        #
        # Draw the form of the target
        #
        self._drawForm(ctx, brush)
        
        #
        # Add letter.
        #
        self._drawLetter(ctx)
    
        #
        # Flush to apply drawing.
        #
        ctx.flush()
    
        img = np.array(img)
        self._templateImg, self._templateAlpha = img[..., :3], img[..., 3].astype(np.float32)/255


    def paste(self, image):
        """Draw the target on an image.
        
        This function uses the parameters of the target and the image to 
        calculate the location and then draw the target on the given image.
        
        Parameters
        ----------
        image : Image object.
            Image on which to draw, should bean object of type AUVSIcv.Image.
        """
        
        #
        # Calculate the transform matrix from the target coordinates to the camera coordinates.
        # 
        M1 = np.array(((1, 0, 0), (0, 1, 0), (0, 0, 0), (0, 0, 1)))
        M2 = np.eye(3, 4)
        M = np.dot(image.K, np.dot(M2, np.dot(np.linalg.inv(image.Rt), np.dot(self._H, M1))))
    
        target = cv2.warpPerspective(self._templateImg, M, dsize=image.img.shape[:2][::-1])
        alpha = cv2.warpPerspective(self._templateAlpha, M, dsize=image.img.shape[:2][::-1])[..., np.newaxis]
    
        img = image.img.astype(np.float32)*(1-alpha) + target[..., :3].astype(np.float32)*alpha
    
        return img.astype(np.uint8)
        

class CircleTarget(BaseTarget):
    """A target in the form of a circle."""
    
    def _drawForm(self, ctx, brush):
        
        ctx.ellipse((0, 0, self._template_size, self._template_size), brush)


