__author__ = 'Ori'

from AUVSIground.auto_detect.classification_runners import CvRunner
from multiprocessing import Process
from os.path import join


database_path = r'C:\Users\User\Documents\auvsi_ftp'


cv_runner = CvRunner(join(database_path, r"resized"),
                     join(database_path, r"images_data"),
                     join(database_path, r"crops"),
                     join(database_path, r"auto_detected"),
                     0.25,
                     server='192.168.1.101',
                     port=8855)

cv_runner._get_suspect_crops()
