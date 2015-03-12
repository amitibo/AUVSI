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

    target = AUVSIcv.PolygonTarget(
        n=5,
        size=2,
        orientation=30,
        altitude=0,
        longitude=32.8167,
        latitude=34.9833, 
        color=(70, 150, 100), 
        letter='A', 
        font_color=(140, 230, 240)
    )
    
    patches = img.createPatches(patch_size=(200, 200), patch_shift=200)
    
    img.pastePatches(patches=patches, target=target)
    
    cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
    for patch in patches:
        patch = cv2.resize(patch, (0, 0), fx=0.1, fy=0.1)
        cv2.imshow('image', patch)
        cv2.waitKey(0)
        
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
    