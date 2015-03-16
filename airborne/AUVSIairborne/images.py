from __future__ import division
from twisted.internet import threads
from twisted.python import log
import multiprocessing as mp
import database as DB
from datetime import datetime
import global_settings as gs
import exifread
import time
import cv2
import os

pool = None

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
    d.addCallback(dispatchImgJob)
    d.addCallback(DB.storeImg)


def getImgData(img_path):

    #
    # give the image some time to finish creation
    #
    time.sleep(2)

    #
    # Get some data from the EXIF
    #
    log.msg('Processing image: {path}'.format(path=img_path))
 
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
    
    time_stamp = tags['Image DateTime'].values.replace(':', '_').replace(' ', '_') + datetime.now().strftime("_%f.jpg")
    new_img_path = os.path.join(gs.RENAMED_IMAGES_FOLDER, time_stamp)
    log.msg('Renaming {old} to {new}'.format(old=img_path, new=new_img_path))
    os.rename(img_path, new_img_path)
    
    img_data = {}
    
    return new_img_path, img_data


def dispatchImgJob(params):
    """Dispatch the image processing task to a process worker."""

    img_path, img_data = params
    
    return pool.apply(processImg, (img_path, img_data))


def processImg(img_path, img_data):
    #
    # sleep to let the image be created.
    #
    time.sleep(0.5)
    img = cv2.imread(img_path)

    #
    # Resize the image.
    #
    resized_img = cv2.resize(img, (0,0), fx=0.25, fy=0.25) 
    
    filename = 'resized_{formated_time}.jpg'.format(
        formated_time=datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
    )
    resized_img_path = os.path.join(gs.RESIZED_IMAGES_FOLDER, filename)
    cv2.imwrite(resized_img_path, resized_img)
    
    return resized_img_path, img_data


def handleNewCrop(img_id, rect):
    """Handle a request for a crop."""
    
    d = threads.deferToThread(getImage, img_id, rect)
    d.addCallback(cropImage)
    
def cropImage(img_path, rect):
    """Crop a rectangle from the full resolution image."""

    img = cv2.imread(img_path)

    #
    # Create the image processing pipeline
    #
    d = threads.deferToThread(getImgData, img_path)
    d.addCallback(dispatchImgJob)
    d.addCallback(DB.storeImg)
    
    
def initIM():
    global pool
    
    pool = mp.Pool(2)
    
    if not os.path.exists(gs.RESIZED_IMAGES_FOLDER):
        os.makedirs(gs.RESIZED_IMAGES_FOLDER)
      
    if not os.path.exists(gs.RENAMED_IMAGES_FOLDER):
        os.makedirs(gs.RENAMED_IMAGES_FOLDER)
          
