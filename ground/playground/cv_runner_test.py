__author__ = 'Ori'

from AUVSIground.auto_detect.classification_runners import CvRunner
from multiprocessing import Process

cv_runner = CvRunner(r"C:\Users\User\Documents\AUVSI\Ori's playground\GS Database\resized",
                     r"C:\Users\User\Documents\AUVSI\Ori's playground\GS Database\images_data",
                     r"C:\Users\User\Documents\AUVSI\Ori's playground\GS Database\crops",
                     r"C:\Users\User\Documents\AUVSI\Ori's playground\GS Database\auto_detected",
                     0.25)

p = Process(target=cv_runner._get_suspect_crops)
p2 = Process(target=cv_runner._classify_crops)
p2.start()
p.start()
