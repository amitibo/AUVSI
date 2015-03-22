""" This script runs on a separate process for each new (image, data)
files. This script is being called in the following way:
    python image_handler.py <original_image_path> <image_data_path>

Running on separate process has higher cpu cores utilization then using
python threads (see: python GIL) and minimizes the interferences to the
airborne services and operations (ftp data sending,
teleoperated system control,image acquiring
"""
__author__ = 'Ori'

from sys import argv
from time import sleep

# STUB for image handler script
#TODO implement pipeline
print "Started handling image: '{}'".format(argv[1])
sleep(5)
print "Finished handling image: '{}'".format(argv[1])