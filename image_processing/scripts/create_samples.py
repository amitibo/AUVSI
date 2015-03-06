from __future__ import division
import AUVSIcv
import numpy as np
import cv2
import glob
import os
import time

def main():

    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = glob.glob(os.path.join(base_path, '*.jpg'))

    img = AUVSIcv.Image(imgs_paths[3])
    
    for i in range(10):
        target = AUVSIcv.CircleTarget(
            size=1,
            orientation=30*i,
            altitude=0,
            longitude=32.8167+0.00001*i,
            latitude=34.9833+0.00001*i, 
            color=(70, 150, 100), 
            letter='A', 
            font_color=(240, 230, 140)
        )
        
        img.paste(target)
    
    cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
    cv2.imshow('image', img.img)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
    