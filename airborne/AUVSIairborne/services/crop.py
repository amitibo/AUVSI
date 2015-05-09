__author__ = 'Ori'

import cv2
import os
import json

class CropImageController(object):
    def __init__(self, images_folder, crops_folder):
        self.images_folder = images_folder
        self.crops_folder = crops_folder

    def __call__(self, cmd):
        """
        :param cmd: a string it the format of
            <timestamp> <x_max> <x_min> <y_max> <y_min>
        :return: None
        """

        area = {}
        timestamp, area['x_max'], area['x_min'],\
            area['y_max'], area['y_min'] = cmd.split()

        int_area = {}
        for key in area.keys():
            int_area[key] = int(area[key])

        self.crop(timestamp, **int_area)

    def _generate_crop_name(self, timestamp):
        """
        :param timestamp: is the timestamp of the image which needs new crop
        :return: a string with name in format of <timestamp>.<crop_num>
        """

        existing_crops = os.listdir(os.path.join(self.crops_folder))
        existing_crops = [crop for crop in existing_crops if crop.endswith(".jpg")]

        crop_nums = []
        for crop in existing_crops:
            orig_time, crop_num, img_format = crop.split('.')
            if orig_time == timestamp:
                crop_nums.append(int(crop_num))

        if not crop_nums:
            next_num = 0
        else:
            next_num = max(crop_nums) + 1

        return timestamp + '.' + str(next_num)

    def crop(self, timestamp, x_min, y_min, x_max, y_max):
        img = cv2.imread(os.path.join(self.images_folder, timestamp + ".jpg"))
        crop_img = img[y_min:y_max, x_min:x_max]

        crop_name = self._generate_crop_name(timestamp)
        crop_path = os.path.join(self.crops_folder, crop_name)
        cv2.imwrite(crop_path + ".jpg", crop_img)

        crop_data = {'x_min': x_min, 'x_max': x_max, 'y_min': y_min,
                     'y_max': y_max}
        with open(crop_path + ".json", 'wb') as f:
            json.dump(crop_data, f)


if __name__ == "__main__":
    area = {'x_min': 100, 'x_max': 300, 'y_min': 100, 'y_max': 300}
    croper = CropImageController(r"C:\Users\Ori\.auvsi_airborne\images",
                                 r"C:\Users\Ori\.auvsi_airborne\crops")
    croper("2015_05_09_01_11_21_235000 300 100 500 100")