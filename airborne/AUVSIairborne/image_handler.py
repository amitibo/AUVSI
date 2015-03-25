""" This script runs on a separate process for each new (image, data)
files. This script is being called in the following way:
    python image_handler.py <original_image_path> <image_data_path>

Running on separate process has higher cpu cores utilization then using
python threads (see: python GIL) and minimizes the interferences to the
airborne services and operations (ftp data sending,
teleoperated system control,image acquiring
"""
__author__ = 'Ori'

from twisted.python import log
from sys import argv
from time import sleep
import os
import cv2
import datetime
import global_settings as gs

#TODO implement pipeline

image_path = argv[1]
log.msg("Started handling image: '{}'".format(image_path))
sleep(0.5)
img = cv2.imread(image_path)

#
# Resize the image.
#
resized_img = cv2.resize(img, (0,0), fx=0.25, fy=0.25)

filename = 'resized_{formated_time}.jpg'.format(
    formated_time=datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
)

resized_img_path = os.path.join(gs.RESIZED_IMAGES_FOLDER, filename)
cv2.imwrite(resized_img_path, resized_img)

log.msg("Finished handling image: '{}'".format(image_path))