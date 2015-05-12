__author__ = 'Ori'

from AUVSIground.auto_detect.classification_runners import CvRunner
from multiprocessing import Process

cv_runner = CvRunner(r"C:\Users\Ori\ftp_playground\resized",
                     r"C:\Users\Ori\ftp_playground\images_data",
                     r"C:\Users\Ori\ftp_playground\crops",
                     r"C:\Users\Ori\ftp_playground\auto_detected",
                     0.25)

p = Process(target=cv_runner._get_suspect_crops)
p2 = Process(target=cv_runner._classify_crops)
p2.start()
p.start()
