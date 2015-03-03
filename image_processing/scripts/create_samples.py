from __future__ import division
import AUVSIcv
import numpy as np
import cv2
import glob
import os

def main():

    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = glob.glob(os.path.join(base_path, '*.jpg'))

    img = AUVSIcv.Image(imgs_paths[0])
    
    target = AUVSIcv.CircleTarget(
        size=1,
        orientation=0,
        altitude=0,
        longitude=32.8167,
        latitud=34.9833, 
        color=(255, 0, 0), 
        letter='A', 
        font_color=(0, 255, 0)
    )
    
    img_target = target.paste(img)
    
    cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
    cv2.imshow('image', img_target)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
    