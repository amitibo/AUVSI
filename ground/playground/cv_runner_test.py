__author__ = 'Ori'

from AUVSIground.auto_detect.mser_iterator import CvRuner

cv_runner = CvRuner(r"C:\Users\Ori\ftp_playground\resized",
                  r"C:\Users\Ori\ftp_playground\images_data",
                  0.25)

cv_runner._get_suspect_crops()