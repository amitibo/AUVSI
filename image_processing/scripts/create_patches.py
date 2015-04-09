from __future__ import division
import AUVSIcv
import numpy as np
import cv2
import glob
import os
import time

def main():

    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = sorted(glob.glob(os.path.join(base_path, '*.jpg')))
    data_paths = [os.path.splitext(path)[0]+'.json' for path in imgs_paths]
    
    #
    # Load image and image data
    #
    img_index = np.random.randint(len(imgs_paths))
    img = AUVSIcv.Image(imgs_paths[img_index], data_path=data_paths[img_index])
    
    patches = img.createPatches(patch_size=(100, 100), patch_shift=50)
        
    samples = []
    for patch in patches:
        target = AUVSIcv.randomTarget(
            altitude=0,
            longitude=img.longitude,
            latitude=img.latitude
        )
        
        img.pastePatch(patch=patch, target=target)

        cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
        cv2.imshow('image', patch)
        
        cv2.waitKey(0)

        patch = cv2.resize(patch, (0, 0), fx=0.15, fy=0.15)
        samples.append(patch.ravel())
        
    samples = np.array(samples)
    
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
    