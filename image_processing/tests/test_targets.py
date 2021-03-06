from __future__ import division
import AUVSIcv
import numpy as np
import json
import cv2
import glob
import os
import time

def main():

    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = glob.glob(os.path.join(base_path, '*.jpg'))

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
        target = AUVSIcv.StarTarget(
            n=5+int(i/3),
            size=2,
            orientation=30*i,
            altitude=0,
            longitude=32.8167+0.00003*i,
            latitude=34.9833+0.00003*i, 
            color=(70, 150, 100), 
            letter='A', 
            font_color=(140, 230, 240)
        )
        
        img.paste(target)
    
    target = AUVSIcv.QRTarget(
        size=2,
        orientation=20,
        altitude=0,
        longitude=32.8167,
        latitude=34.9833,
        text='www.google.com'
    )

    img.paste(target)
    
    cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
    cv2.imshow('image', img.img)
    
    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
    