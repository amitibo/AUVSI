__author__ = 'Ori'

from AUVSIground.auto_detect.classification_runners import MserRunner, CropsRetriver
from time import sleep

#
# it = MserIterator(r"C:\Users\Ori\ftp_playground\resized",
#                   r"C:\Users\Ori\ftp_playground\images_data",
#                   0.25)
# while True:
#     try:
#         (time, res) = it.next()
#         print("The results for image: " + time)
#         print(str(res) + "\n")
#     except:
#         pass
#
#     sleep(2)

runer = MserRunner(r"C:\Users\Ori\ftp_playground\resized",
                  r"C:\Users\Ori\ftp_playground\images_data",
                  0.25)
croper = CropsRetriver(None, 'localhost')

while True:

    try:
        timestamp, res = runer.mser_one_image()
        print(timestamp)

        if res == -1:
            continue

        for row in res:
            area = {"x_max": row[2],
                    "x_min": row[3],
                    "y_max": row[4],
                    "y_min": row[5]}

            croper.get_crop(timestamp, area)
    except TypeError:
        pass
    finally:
        sleep(0.5)