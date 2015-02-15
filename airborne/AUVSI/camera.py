from __future__ import division
import global_settings as gs
import numpy as np
from datetime import datetime
import Image
import time

import os


class BaseCamera(object):
    def __init__(self):
        #
        # 
        #
        self.base_path = gs.IMAGES_FOLDER
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _getName(self):
        filename = '{formated_time}.jpg'.format(
            formated_time=datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        )
        
        return os.path.join(self.base_path, filename)
        
    
class MockupCamera(BaseCamera):
    
    def shoot(self, callback):
        print 'Shooting'

        A = np.random.randint(low=0, high=255, size=(480, 640)).astype(np.uint8)
        
        capture_path = self._getName()

        img = Image.fromarray(A)
        img.save(capture_path)

        callback(capture_path)
        
