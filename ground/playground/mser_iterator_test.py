__author__ = 'Ori'

from AUVSIground.auto_detect.mser_iterator import MserIterator
from time import sleep


it = MserIterator(r"C:\Users\Ori\ftp_playground\resized",
                  r"C:\Users\Ori\ftp_playground\images_data",
                  0.25)
while True:
    try:
        (time, res) = it.next()
        print("The results for image: " + time)
        print(str(res) + "\n")
    except:
        pass

    sleep(2)
