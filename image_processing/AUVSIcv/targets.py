from __future__ import division
import numpy as np
import transformation_matrices as transforms
import aggdraw
import Image
from .NED import NED
import cv2
import math


__all__ = [
    "CircleTarget",
]


class BaseTarget(object):
    """
    Base target from which all other target inherit.
    
    size: float
        Size of target in meters.
    orientation: float
        Orientation of the target (degrees) in respect to the north.
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
        
        #
        # Note:
        # For some reason I have add 90 degrees to the orientation to make the coords behave correctly.
        #
        self._size = size
        self._orientation = math.radians(orientation+90)
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
        
    def H(self, latitude, longitude, altitude):
        """Calculate the transform of the target.
        
        Calculate the cartesian coordinate transform relative to a given lat, lon, alt coords.
        
        Parameters
        ----------
        latitude, longitude, altitude: three tuple of floats
            Center of the cartesian coordinate system (e.g. camera center). The transform
            uses the local cartesian coordinate system (North East Down). Makes use of code
            from the COLA2 project (https://bitbucket.org/udg_cirs/cola2).            
        """
        ned = NED(lat=latitude, lon=longitude, height=altitude)
        T = transforms.translation_matrix(ned.geodetic2ned((self._latitude, self._longitude, self._altitude)))
        R = transforms.euler_matrix(self._orientation, 0, 0, 'szxy')
        S = transforms.scale_matrix(self._size/self._template_size)
    
        return np.dot(T, np.dot(R, S))
    
    @property
    def img(self):
        return self._templateImg
    
    @property
    def alpha(self):
        return self._templateAlpha
    

class CircleTarget(BaseTarget):
    """A target in the form of a circle."""
    
    def _drawForm(self, ctx, brush):
        
        ctx.ellipse((0, 0, self._template_size, self._template_size), brush)


