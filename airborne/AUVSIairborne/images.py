from __future__ import division
from twisted.internet import threads
from twisted.python import log
import multiprocessing as mp
import database as DB
from datetime import datetime
import global_settings as gs
import PixHawk as PH
import AUVSIcv
import json
import time
import cv2
import os

pool = None

def tagRatio(tag):
    ratio = tag.values[0].num/tag.values[0].den
    return ratio


def tagValue(tag):
    return tag.values[0]


def handleNewImage(img_path, timestamp):
    #
    # Create the image processing pipeline
    #
    d = threads.deferToThread(dispatchImgJob, img_path, timestamp)
    d.addCallback(saveFlightData)
    d.addCallback(DB.storeImg)


def dispatchImgJob(params):
    """Dispatch the image processing task to a process worker."""
    
    img_path, timestamp = params
    
    log.msg('Dispatching new image {img}'.format(img=img_path))
    
    return pool.apply(processImg, (img_path, timestamp))


def processImg(img_path, timestamp):
    """
    Do all image processing actions. Should be called on a separate process to allow mutli processesors.
    Currently does only resizing.
    """
    
    #
    # give the image some time to finish creation
    #
    time.sleep(1)

    #
    # Load the image
    #
    log.msg('Loading new image {img}'.format(img=img_path))    
    img = AUVSIcv.Image(img_path, timestamp=timestamp)
    
    #
    # Rename it with time stamp.
    #
    new_img_path = os.path.join(gs.RENAMED_IMAGES_FOLDER, img.datetime+'.jpg')
    
    log.msg('Renaming {old} to {new}'.format(old=img_path, new=new_img_path))
    os.rename(img_path, new_img_path)
    
    #
    # Resize the image.
    #
    log.msg('Resizing new image {img}'.format(img=new_img_path))
    
    resized_img = cv2.resize(img.img, (0,0), fx=0.25, fy=0.25) 
    filename = 'resized_{path}'.format(path=os.path.split(new_img_path)[1])
    
    resized_img_path = os.path.join(gs.RESIZED_IMAGES_FOLDER, filename)
    cv2.imwrite(resized_img_path, resized_img)
    
    return resized_img_path, img.datetime, img.K


def saveFlightData(params):
    
    img_path, timestamp, K = params
    
    #
    # Get the closest time stamp and save it with the image.
    #
    flight_data = PH.queryPHdata(timestamp)
    flight_data['K']=K.tolist()
    flight_data_path = os.path.splitext(img_path)[0]+'.json'
    with open(flight_data_path, 'wb') as f:
        json.dump(flight_data, f)

    return img_path, {}

    
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
          
