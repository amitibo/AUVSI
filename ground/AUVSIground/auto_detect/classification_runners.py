__author__ = 'Ori'

from AUVSIcv.Mser_Color_Scaled_Down import MSER_Primary
from AUVSIairborne.file_scheduler import FileScheduler
import os
import cv2
import json
import bisect
from time import sleep
import telnetlib
from AUVSIcv import global_settings
from multiprocessing import Process
from AUVSIcv.Target_ID import Target_Flow


class CvRunner(object):
    def __init__(self, images_folder, data_folder, crops_folder,
                 results_dir, scale_down, server='localhost', port=8844):
        self.mser = MserRunner(images_folder, data_folder, scale_down)
        self.croper = CropsRetriver(crops_folder, server, port)
        self.classifier = TargetFlowRunner(crops_folder)
        self.targets_found = 0
        self._proc_mser = Process(target=self._get_suspect_crops)
        self._proc_classification = Process(target=self._classify_crops)

        try:
            os.makedirs(results_dir)
        except WindowsError:
            pass
        finally:
            self.results_dir = results_dir

    def run(self):
        self._proc_mser.start()
        self._proc_classification.start()

        self._proc_mser.join()
        self._proc_classification.join()

    def _dump_target_data(self, data):
        if not data:
            return

        self.targets_found += 1
        data_file_name = str(self.targets_found) + ".json"
        data_file_path = os.path.join(self.results_dir, data_file_name)

        with open(data_file_path, 'wb') as f:
            json.dump(data, f)

    def _classify_crops(self):
        while True:
            print("Classifying!")
            try:
                res = self.classifier.classify_one_crop()

                self._dump_target_data(res)
            except:
                pass
            finally:
                sleep(0.5)

    def _get_suspect_crops(self):
        while True:
            print("Mser!")
            try:
                self._get_crops_one_image()
            except TypeError:
                pass
            finally:
                sleep(0.5)

    def _get_crops_one_image(self):
        timestamp, res = self.mser.mser_one_image()
        area_list = CvRunner._mser_to_area(res)

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


class TargetFlowRunner(object):
    def __init__(self, crop_folder):
        self.crop_scheduler = FileScheduler(crop_folder)

    def classify_one_crop(self):
        for f in self.crop_scheduler:
            try:
                timestamp, crop_id, extension = f.split('.')
            except ValueError:
                continue

            if extension != "jpg":
                continue

            crop_path = os.path.join(self.crop_scheduler.dir_path, f)
            crop_image = cv2.imread(crop_path)

            flow_res = Target_Flow(crop_image,
                                   global_settings.Shape_Name_DB_Path,
                                   global_settings.SHAPE_DB_PATH,
                                   global_settings.Letter_Name_DB_Path,
                                   global_settings.Letter_DB_Path)

            if not flow_res:
                continue

            flow_res['timestamp'] = timestamp
            flow_res['crop_id'] = crop_id
            flow_res['crop_path'] = crop_path

            return flow_res


class MserRunner(object):
    def __init__(self, images_folder, data_folder, scale_down):
        self.image_scheduler = FileScheduler(images_folder)
        self.data_folder = data_folder
        self.scale_down = scale_down

    def mser_one_image(self):
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
            image_info['Flight_Altitude'] = image_info['relative_alt']*3.28/(1e3)
            sleep(1)
            return timestamp, MSER_Primary(image, image_info,
                                           self.scale_down, None)

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
    def __init__(self, dest_dir, server, port=8844):
        self.dest_dir = dest_dir
        self.server = server
        self.port = port

    def get_crop(self, timestamp, area):
        """
        Sends request for crop
        :param timestamp: the image timestamp
        :param area: dictionary with keys "x_max", "x_min", "y_max", "y_min"
        :return:
        """
        delimiter = b'\r\n'

        tl = telnetlib.Telnet(host=self.server, port=self.port)

        area = {key: int(area[key]) for key in area}

        cmd = "crop {timestamp} {x_max} {x_min} {y_max} {y_min}".format(
            timestamp=timestamp, **area)


        print(cmd)
        tl.write(cmd + delimiter)
        tl.read_until("More")
        tl.close()