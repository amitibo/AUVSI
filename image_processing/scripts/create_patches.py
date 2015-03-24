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

    #
    # Load image data
    #
    data_path = os.path.splitext(imgs_paths[3])[0]+'.txt'
    with open(data_path, 'r') as f:
        data = json.load(f)
        
    img.calculateExtrinsicMatrix(
        latitude=data['latitude'],
        longitude=data['longitude'],
        altitude=data['altitude'],
        yaw=data['yaw'],
        pitch=data['pitch'],
        roll=data['roll'],
    )

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
    
    patches = img.createPatches(patch_size=(200, 200), patch_shift=50)
        
    samples = []
    for patch in patches:
        img.pastePatch(patch=patch, target=target)
        
        patch = cv2.resize(patch, (0, 0), fx=0.15, fy=0.15)
        samples.append(patch.ravel())
        
    samples = np.array(samples)
    
    pass


if __name__ == '__main__':
    main()
    