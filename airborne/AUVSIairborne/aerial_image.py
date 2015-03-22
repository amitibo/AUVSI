""" An API to manipulate the aerial images database (filesystem base)
"""

#TODO Implement this API
__author__ = 'Ori'

import json


class AerialImage(object):
    """ Representation of an aerial image which goes through the image
     processing pipeline and downstream sending.
    """

    def __init__(self, path):
        """:param path: the path of the original image"""
        self.path = {'original': path,
                     'lowRes': None,
                     'data': None}

    def append_data(self, data, data_path):
        #TODO Impliment append_data with a common folder to the original...
        # or maybe in a dedicated folder (some kind of a manager?)
        if self.path['data'] is not None:
            #TODO raising an exception may be needed
            return
        with open(data_path, 'w') as f:
            json.dump(data, f)
        self.path['data'] = data_path

