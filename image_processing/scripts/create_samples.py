from __future__ import division
import numpy as np
import cv2
import aggdraw
import Image


def createTargetAgg(shape, size, color, letter):
    
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

    
def main():

    img = cv2.imread('../data/IMG_4487.jpg')#[:800, :800, ...]
    
    target, alpha = createTargetAgg(shape='circle', size=130, color=(0, 0, 255), letter='R')
    img = pasteTarget(img, target, alpha, location=(930, 2490))
    
    cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
    cv2.imshow('image', img)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
    