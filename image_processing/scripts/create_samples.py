from __future__ import division
import AUVSIcv
import numpy as np
import cv2
import glob
import os
import time
import json


def main():

    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = glob.glob(os.path.join(base_path, '*.jpg'))

    #
    # Load image and image data
    #
    img = AUVSIcv.Image(imgs_paths[3])
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
    
    for i in range(10):
        target = AUVSIcv.randomTarget(
            altitude=0,
            longitude=32.8167,
            latitude=34.9833
        )
        
        img.paste(target)
    
    cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
    resized_img = cv2.resize(img.img, (0, 0), fx=0.25, fy=0.25)
    
    cv2.imshow('image', resized_img)
    cv2.imwrite('image_with_targets.jpg', img.img)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
    