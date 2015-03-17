from __future__ import division
import numpy as np
import transformation_matrices as transforms
import aggdraw
import Image
from .NED import NED
import cv2
import math
import tempfile
import shutil
import os


__all__ = [
    "CircleTarget",
    "RectangleTarget",
    "TriangleTarget",
    "CrossTarget",
    "PolygonTarget",
    "StarTarget",
    "QRTarget"
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
        font=None,
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
        if font is None:
            import platform
            if platform.system() == 'Linux':
                self._font = r"/usr/share/fonts/truetype/freefont/FreeSans.ttf"
            else:
                self._font = r"C:\Windows\Fonts\Arialbd.ttf"
        else:
            self._font = font
        print 'FONT:', self._font

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
        if self._letter is not None:
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
        T1 = transforms.translation_matrix((-self._template_size/2, -self._template_size/2, 0))
        S = transforms.scale_matrix(self._size/self._template_size)
        R = transforms.euler_matrix(self._orientation, 0, 0, 'szxy')
        T2 = transforms.translation_matrix(ned.geodetic2ned((self._latitude, self._longitude, self._altitude)))
    
        return np.dot(T2, np.dot(R, np.dot(S, T1)))
    
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


class RectangleTarget(BaseTarget):
    """A target in the form of a rectangle."""

    def _drawForm(self, ctx, brush):

        ctx.rectangle((0, 0, self._template_size, self._template_size), brush)


class TriangleTarget(BaseTarget):
    """A target in the form of a triangle."""

    def _drawForm(self, ctx, brush):

        ctx.polygon((0, self._template_size, self._template_size, self._template_size, self._template_size/2, 0), brush)


class CrossTarget(BaseTarget):
    """A target in the form of a cross."""

    def _drawForm(self, ctx, brush):

        ctx.polygon(
            (
                0, self._template_size/3,
                0, self._template_size*2/3,
                self._template_size/3, self._template_size*2/3,
                self._template_size/3, self._template_size,
                self._template_size*2/3, self._template_size,
                self._template_size*2/3, self._template_size*2/3,
                self._template_size, self._template_size*2/3,
                self._template_size, self._template_size/3,
                self._template_size*2/3, self._template_size/3,
                self._template_size*2/3, 0,
                self._template_size/3, 0,
                self._template_size/3, self._template_size/3
                ),
            brush
        )


class PolygonTarget(BaseTarget):
    """A target in the form of a n-sided polygon."""

    def __init__(self, n, *args, **kwds):
        
        self._nsides = n
        
        super(PolygonTarget, self).__init__(*args, **kwds)
        
    def _drawForm(self, ctx, brush):

        r = self._template_size/2
        alpha = np.pi*2/self._nsides
        
        polygon = []
        for i in range(self._nsides):
            polygon.append(r + r*np.cos(alpha*i))
            polygon.append(r + r*np.sin(alpha*i))
            
        ctx.polygon(polygon, brush)


class StarTarget(BaseTarget):
    """A target in the form of a n-star."""

    def __init__(self, n, *args, **kwds):
        
        self._nstar = n
        
        super(StarTarget, self).__init__(*args, **kwds)
        
    def _drawForm(self, ctx, brush):

        r_outer = c = self._template_size/2
        r_inner = self._template_size/4
        alpha = np.pi/self._nstar
        
        polygon = []
        for i in range(2*self._nstar):
            if i % 2 == 1:
                r = r_outer
            else:
                r = r_inner
                
            polygon.append(c + r*np.cos(alpha*i))
            polygon.append(c + r*np.sin(alpha*i))
            
        ctx.polygon(polygon, brush)


class QRTarget(BaseTarget):
    """A target in the form of a circle."""

    def __init__(
        self,
        size,
        orientation,
        altitude,
        longitude,
        latitude,
        text,
        template_size=400
        ):

        self._text = text

        super(QRTarget, self).__init__(
            size,
            orientation,
            altitude,
            longitude,
            latitude,
            color=None,
            letter=None,
            font_color=None,
            )
        

    def _drawTemplate(self):
        """Draw the target on the base template"""

        import pyqrcode
        
        qr = pyqrcode.create(self._text)
        qr_size = qr.get_png_size(scale=1)
        scale = int(self._template_size/qr_size+0.5)
        self._template_size = qr.get_png_size(scale=scale)
        
        base_path = tempfile.mkdtemp()
        img_path = os.path.join(base_path, 'temp.png')
        
        qr.png(img_path, scale=scale)
        
        img = cv2.imread(img_path)
        
        shutil.rmtree(base_path)
        
        self._templateImg = img
        self._templateAlpha = np.ones(img.shape[:2], dtype=np.float32)

