from __future__ import division
import AUVSIcv
import numpy as np
import cv2
import glob
import os
import time
from AUVSIcv import MSER
import time


def main():
    
    base_path = os.environ['AUVSI_CV_DATA']
    imgs_paths = glob.glob(os.path.join(base_path, '*.jpg'))

    img = AUVSIcv.Image(imgs_paths[0])

    for i in range(10):
        target = AUVSIcv.PolygonTarget(
            n=5+int(i/3),
            size=1.5,
            orientation=30*i,
            altitude=190,
            longitude=32.8168-0.00003*i,
            latitude=34.9836-0.00003*i, 
            color=(10*i, 250 - 10*i, 250-5*i), 
            letter='E', 
            font_color=(140, 230, 240)
        )

        img.paste(target)

    #target = AUVSIcv.QRTarget(
        #size=2,
        #orientation=20,
        #altitude=0,
        #longitude=32.8167,
        #latitude=34.9833,
        #text='www.google.com'
    #)

    #img.paste(target)

    Image_Information = {'Focal_Length': 5, 'Flight_Altitude': 190, 'Camera_Pitch_Angle': 0, 'Camera_Roll_Angle' : 0}
    Image = img.img
    Scaling_Constant = 0.25
    
    file_name = os.path.splitext(os.path.split(__file__)[1])[0]
    results_path = os.path.abspath(os.path.join('results', file_name))
    if not os.path.exists(results_path):
        os.makedirs(results_path)
    
    start = time.time()
    MSER.MSER_primary(Image,Image_Information,Scaling_Constant,results_path)
    end = time.time()
    print end - start  
    
    cv2.namedWindow('image', flags=cv2.WINDOW_NORMAL)
    cv2.imshow('image', img.img)
    cv2.imwrite('image_with_targets.png', img.img)

    cv2.waitKey(0)
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()