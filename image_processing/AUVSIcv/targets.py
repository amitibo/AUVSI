import aggdraw
import Image


__all__ = [
    "",
]


class BaseTarget(object):
    """Base target frome which all other target inherit."""
    
    def __init__(
        self,
        size,
        orientation,
        position,
        color,
        letter,
        letter_color,
        font
        ):
        
        self._size = size
        self._orientation = orientation
        self._position = position
        self._color = color
        self._letter = letter
        self._letter_color = letter_color
        self._font = font
    
    def paste(
        self,
        image,
        height,
        zoom,
        
        ):
def createTarget(shape, size, color, letter):

    img = Image.new(mode='RGBA', size=(size, size), color=(0, 0, 0, 0))
    ctx = aggdraw.Draw(img)
    brush = aggdraw.Brush((100, 150, 70), 255)

    ctx.ellipse((0, 0, size, size), brush)

    #
    # Add letter.
    #
    font = aggdraw.Font((140, 230, 240), r"C:\Windows\Fonts\Arialbd.ttf", 60) 
    ctx.text((50, 50), letter, font)    

    ctx.flush()

    img = np.array(img)
    img, alpha = img[..., :3], img[..., 3].astype(np.float32)/255

    return img, alpha


def pasteTarget(img, target, alpha, location):
    M = np.eye(3, dtype=np.float32)
    M[:2, 2] = location

    target = cv2.warpPerspective(target, M, dsize = img.shape[:2][::-1])
    alpha = cv2.warpPerspective(alpha, M, dsize = img.shape[:2][::-1])[..., np.newaxis]

    img = img.astype(np.float32)*(1-alpha) + target[..., :3].astype(np.float32)*alpha

    return img.astype(np.uint8)



