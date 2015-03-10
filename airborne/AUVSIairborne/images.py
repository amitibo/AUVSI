from __future__ import division
from twisted.internet import threads
import database as DB
from datetime import datetime
import global_settings as gs
import exifread
import time
import cv2
import os


def tagRatio(tag):
    ratio = tag.values[0].num/tag.values[0].den
    return ratio


def tagValue(tag):
    return tag.values[0]


def handleNewImage(img_path):
    #
    # Create the image processing pipeline
    #
    d = threads.deferToThread(getImgData, img_path)
    d.addCallback(resizeImg)
    d.addCallback(createCrops)
    d.addCallback(DB.storeImg)


def getImgData(img_path):
    #
    # Get some data from the EXIF
    #
    with open(img_path, 'rb') as f:
        tags = exifread.process_file(f)

    #
    # Calculate camera intrinsic matrix.
    #
    in_to_mm = 25.4
    #FocalPlaneYResolution = tagRatio(tags['EXIF FocalPlaneYResolution'])
    #FocalPlaneXResolution = tagRatio(tags['EXIF FocalPlaneXResolution'])
    #ImageLength = tagValue(tags['EXIF ExifImageLength'])
    #ImageWidth = tagValue(tags['EXIF ExifImageWidth'])
    #FocalLength = tagRatio(tags['EXIF FocalLength'])

    img_data = {}
    
    return img_path, img_data


def resizeImg(params):
    #
    #
    #
    img_path, img_data = params
    
    #
    # sleep to let the image be created.
    #
    time.sleep(0.5)
    img = cv2.imread(img_path)
    resized_img = cv2.resize(img, (0,0), fx=0.5, fy=0.5) 
    
    if not os.path.exists(gs.RESIZED_IMAGES_FOLDER):
        os.makedirs(gs.RESIZED_IMAGES_FOLDER)
    
    filename = 'resized_{formated_time}.jpg'.format(
        formated_time=datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    )
    resized_img_path = os.path.join(gs.RESIZED_IMAGES_FOLDER, filename)
    cv2.imwrite(resized_img_path, resized_img)
    
    return resized_img_path, img_data


def createCrops(params):
    #
    #
    #
    img_path, img_data = params
    
    return img_path, img_data

