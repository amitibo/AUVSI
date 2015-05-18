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
from datetime import datetime
import global_settings as gs
import exifread
import json
from bisect import bisect
import shutil

image_path = argv[1]

#
# Read image
#
log.msg("Started handling image: '{}'".format(image_path))
sleep(0.5)
img = cv2.imread(image_path)
with open(image_path, 'rb') as f:
    tags = exifread.process_file(f)

formated_time=datetime.now().strftime(gs.BASE_TIMESTAMP)

#
# Rename original image and add timestamp
#
renamed_image_path = os.path.join(gs.IMAGES_RENAMED, formated_time + ".jpg")
os.rename(image_path, renamed_image_path)

#
# Resize the image.
#

resized_img = cv2.resize(img, (0, 0), fx=0.25, fy=0.25)
filename = '{formated_time}.resized.jpg'.format(formated_time=formated_time)

resized_img_path = os.path.join(gs.RESIZED_IMAGES_FOLDER, filename)
cv2.imwrite(resized_img_path, resized_img)

#
# Extract Exif data
#
# exif_file = os.path.join(gs.IMAGES_DATA, formated_time + ".exif.json")
# with open(exif_file, 'wb') as data_file:
#         json.dump(tags, data_file)


#
# Acquire data
#

data_list = sorted(os.listdir(gs.FLIGHT_DATA_FOLDER))
data_index = bisect(data_list, formated_time)
data_index = max(data_index-1, 0)
data_path = os.path.join(gs.FLIGHT_DATA_FOLDER, data_list[data_index])

image_data_path = os.path.join(gs.IMAGES_DATA,
                               "{time}.json".format(time=formated_time))
shutil.copy(data_path, image_data_path)

log.msg("Finished handling image: '{}'".format(image_path))