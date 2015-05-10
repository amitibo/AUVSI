__author__ = 'Ori'

from AUVSIcv.Mser_Color_Scaled_Down import MSER_Primary
from AUVSIairborne.file_scheduler import FileScheduler
import os
import cv2
import json
import bisect
from time import sleep
import telnetlib


class CvRuner(object):
    def __init__(self, images_folder, data_folder,
                 scale_down, server='localhost'):
        self.mser = MserRuner(images_folder, data_folder, scale_down)
        self.croper = CropsRetriver(None, server)

    def _get_suspect_crops(self):
        while True:
            try:
                self._get_crops_one_image()
            except TypeError:
                pass
            finally:
                sleep(0.5)

    def _get_crops_one_image(self):
        timestamp, res = self.mser.run()
        area_list = CvRuner._mser_to_area(res)

        for area in area_list:
            self.croper.get_crop(timestamp, area)

    @staticmethod
    def _mser_to_area(mser_results):
        """
        converts the mser results matrix to an area dictionary
        """
        area_list = []
        try:
            for row in mser_results:
                area_list.append({"x_max": row[2],
                            "x_min": row[3],
                            "y_max": row[4],
                            "y_min": row[5]})
        except TypeError:
            return None

        return area_list


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
            sleep(1)
            return timestamp, MSER_Primary(image, image_info, self.scale_down, None)

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
        delimiter = b'\r\n'

        tl = telnetlib.Telnet(host=self.server, port=8844)

        area = {key: int(area[key]) for key in area}

        cmd = "crop {timestamp} {x_max} {x_min} {y_max} {y_min}".format(
            timestamp=timestamp, **area)


        print(cmd)
        tl.write(cmd + delimiter)
        tl.read_until("More")
        tl.close()