""" This script runs on a separate process for each new (image, data)
files. This script is being called in the following way:
    python image_handler.py <original_image_path> <image_data_path>

Running on separate process has higher cpu cores utilization then using
python threads (see: python GIL) and minimizes the interferences to the
airborne services and operations (ftp data sending,
teleoperated system control,image acquiring
"""
__author__ = 'Ori'

IMAGE_RESIZE_RATIO = 0.25
IMAGE_RESIZE_MATRIX = np.array(((IMAGE_RESIZE_RATIO, 0, 0),
                                (0, IMAGE_RESIZE_RATIO, 0),
                                (0, 0, 1)))


import numpy as np
from twisted.python import log
from sys import argv
from time import sleep
import os
import cv2
import AUVSIcv
from datetime import datetime
import global_settings as gs
from bisect import bisect
import shutil
import json

image_path = argv[1]

# Wait for image to fully be on disk
sleep(0.5)

#
# Load image
#
formatted_time = datetime.now().strftime(gs.BASE_TIMESTAMP)
log.msg("Started handling image: '{}'".format(image_path))
log.msg('Loading new image {img}'.format(img=image_path))
img = AUVSIcv.Image(image_path, timestamp=formatted_time)

#
# Rename image to include timestamp
#
formatted_path = os.path.join(gs.IMAGES_RENAMED, formatted_time + ".jpg")
log.msg('Renaming {old} to {new}'.format(old=image_path, new=formatted_path))

os.rename(image_path, formatted_path)

#
# Resize the image.
#
resized_img = cv2.resize(img.img, (0, 0), fx=IMAGE_RESIZE_RATIO,
                         fy=IMAGE_RESIZE_RATIO)

resized_filename = '{formated_time}.resized.jpg'.format(formated_time=formatted_time)
resized_img_path = os.path.join(gs.RESIZED_IMAGES_FOLDER, resized_filename)
cv2.imwrite(resized_img_path, resized_img)
log.msg("Resized image {time}".format(time=formatted_time))

#
# Get data for resized image
#
data_list = sorted(os.listdir(gs.FLIGHT_DATA_FOLDER))
index = bisect(data_list, formatted_time)
r_index = max(index - 1, 0)

data_name = data_list[r_index]

image_data_path = os.path.join(gs.IMAGES_DATA, formatted_time + '.json')
shutil.copy(os.path.join(gs.FLIGHT_DATA_FOLDER, data_name),
            image_data_path)
log.msg("Acquired data {orig_data_name} for image {resized_name}"
        .format(orig_data_name=data_name, resized_name=resized_filename))

#
# Add the resized K matrix to the image data
#
resized_k = np.dot(IMAGE_RESIZE_MATRIX, img.K)

with open(image_data_path, 'rb') as data_file:
    image_data = json.load(data_file)

image_data['K'] = resized_k.tolist()
image_data['resized_K'] = True

with open(image_data_path, 'wb') as data_file:
    json.dump(image_data, data_file)

log.msg("Finished handling image with timestamp: '{}'".format(formatted_time))
