from __future__ import division
import numpy as np
import cv2

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
    