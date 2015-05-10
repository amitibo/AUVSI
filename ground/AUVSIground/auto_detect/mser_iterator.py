__author__ = 'Ori'

from AUVSIcv.Mser_Color_Scaled_Down import MSER_Primary
import os
import cv2
import json
import bisect


class MserIterator(object):
    def __init__(self, images_folder, data_folder, scale_down):
        self.images_folder = images_folder
        self.data_folder = data_folder
        self.scale_down = scale_down
        self.current_timestamp = None

    def __iter__(self):
        return self

    def _get_timestamps_list(self):
        """
        :return: a list of timestamps for the currently accessible images
        """
        file_list = os.listdir(self.images_folder)
        return sorted([f.split('.')[0] for f in file_list])

    def next(self):
        """
        :return: (image_timestamp, mser_result)
        """
        timestamps = self._get_timestamps_list()
        if not self.current_timestamp:
            try:
                self.current_timestamp = timestamps[0]
                return self.current_timestamp, self._mser_current()
            except IndexError:
                raise StopIteration()

        current_index = timestamps.index(self.current_timestamp)
        try:
            self.current_timestamp = timestamps[current_index + 1]
        except IndexError:
            raise StopIteration()

        try:
            mser_result = self._mser_current()
        except cv2.error:
            mser_result = -1

        return self.current_timestamp, mser_result

    @property
    def _current_image_path(self):
        image_name = self.current_timestamp + '.resized.jpg'
        return os.path.join(self.images_folder, image_name)

    @property
    def _current_data_path(self):
        data_list = sorted(os.listdir(self.data_folder))
        data_index = bisect.bisect(data_list, self.current_timestamp)
        r_index = max(data_index-1, 0)
        data_name = data_list[r_index]

        return os.path.join(self.data_folder, data_name)

    def _mser_current(self):
        image = cv2.imread(self._current_image_path)

        with open(self._current_data_path) as f:
            image_info = json.load(f)

        image_info['Focal_Length'] = 5
        image_info['Flight_Altitude'] = image_info['relative_alt']
        return MSER_Primary(image, image_info, 0.25, None)

