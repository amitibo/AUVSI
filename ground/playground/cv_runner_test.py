__author__ = 'Ori'

from AUVSIground.auto_detect.classification_runners import CvRunner


cv_runner = CvRunner(r"C:\Users\Ori\ftp_playground\resized",
                     r"C:\Users\Ori\ftp_playground\images_data",
                     r"C:\Users\Ori\ftp_playground\crops",
                     r"C:\Users\Ori\ftp_playground\auto_detected",
                     0.25)

cv_runner._classify_crops()