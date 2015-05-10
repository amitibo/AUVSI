__author__ = 'Ori'

from AUVSIcv.Mser_Color_Scaled_Down import MSER_Primary
from AUVSIairborne.file_scheduler import FileScheduler
import os
import cv2
import json
import bisect
from time import sleep
import socket


class MserRuner(object):
    def __init__(self, images_folder, data_folder, scale_down):
        self.image_scheduler = FileScheduler(images_folder)
        self.data_folder = data_folder
        self.scale_down = scale_down

    def run(self):
        for f in self.image_scheduler:
            try:
                timestamp, _, extension = f.split('.')
            except ValueError:
                continue

            if extension != "jpg":
                continue

            image_path = os.path.join(self.image_scheduler.dir_path, f)
            image = cv2.imread(image_path)

            with open(self._data_path(timestamp)) as j:
                image_info = json.load(j)

            image_info['Focal_Length'] = 5
            image_info['Flight_Altitude'] = image_info['relative_alt']
            sleep(0.5)
            return f, MSER_Primary(image, image_info, self.scale_down, None)

    def _data_path(self, timestamp):
        data_list = sorted(os.listdir(self.data_folder))
        data_index = bisect.bisect(data_list, timestamp)
        r_index = max(data_index-1, 0)
        data_name = data_list[r_index]

        return os.path.join(self.data_folder, data_name)


class CropsRetriver(object):
    """
    This object manages the download of full resolution crops
    from the aerial system.
    """
    def __init__(self, dest_dir, server):
        self.dest_dir = dest_dir
        self.server = server

    def get_crop(self, timestamp, area):
        """
        Sends request for crop
        :param timestamp: the image timestamp
        :param area: dictionary with keys "x_max", "x_min", "y_max", "y_min"
        :return:
        """
        s = socket.socket()
        s.connect((self.server, 8844))

        cmd = "crop {timestamp} {x_max} {x_min} {y_max} {y_min}".format(
            timestamp=timestamp, **area)

        s.send(cmd)
        s.recv(1)
        s.close()