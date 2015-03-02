import aggdraw
import Image


__all__ = [
    "",
]


class BaseTarget(object):
    """Base target from which all other target inherit."""
    
    def __init__(
        self,
        size,
        orientation,
        longitude,
        latitude,
        color,
        letter,
        letter_color,
        font=r"C:\Windows\Fonts\Arialbd.ttf"
        ):
        
        self._size = size
        self._orientation = orientation
        self._longitude = longitude
        self._latitude = latitude
        self._color = color
        self._letter = letter
        self._letter_color = letter_color
        self._font = font
    
    def _drawLetter(self, ctx):
        """Draw the letter on the target.
        
        This function is called after the target has been drawn.

        Parameters
        ----------
        ctx: aggdraw context
            The context to drawon.
        """
        font = aggdraw.Font((140, 230, 240), self._font, 60) 
        ctx.text((50, 50), self._letter, font)    

    def paste(self, image):
        """Draw the target on an image.
        
        This function uses the parameters of the target and the image to 
        calculate the location and then draw the target on the given image.
        
        Parameters
        ----------
        image : Image object.
            Image on which to draw, should bean object of type AUVSIcv.Image.
        """
        
        M = np.eye(3, dtype=np.float32)
        M[:2, 2] = location
    
        target = cv2.warpPerspective(target, M, dsize = img.shape[:2][::-1])
        alpha = cv2.warpPerspective(alpha, M, dsize = img.shape[:2][::-1])[..., np.newaxis]
    
        img = img.astype(np.float32)*(1-alpha) + target[..., :3].astype(np.float32)*alpha
    
        return img.astype(np.uint8)
        

class CircleTarget(BaseTarget):
    """A target in the form of a circle."""
    
    def _drawForm(self):
        
        img = Image.new(mode='RGBA', size=(size, size), color=(0, 0, 0, 0))
        ctx = aggdraw.Draw(img)
        brush = aggdraw.Brush((100, 150, 70), 255)
    
        ctx.ellipse((0, 0, size, size), brush)

        #
        # Add letter.
        #
        self._drawLetter(ctx)
        
        #
        # Flush to apply drawing.
        #
        ctx.flush()
    
        img = np.array(img)
        img, alpha = img[..., :3], img[..., 3].astype(np.float32)/255
    

