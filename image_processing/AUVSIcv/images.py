from __future__ import division
import cv2
import json
import os


class Image(object):
    def __init__(self, img_path):
        
        self._img = cv2.imread(img_path)
        data_path = os.path.splitext(img_path)[0]+'.txt'
        with open(data_path, 'r') as f:
            self._data = json.load(f)

    