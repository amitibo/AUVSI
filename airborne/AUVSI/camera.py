from __future__ import division
import numpy as np
import Image
import time

import os


class MockupCamera(object):
    
    def __init__(self, base_path='~/images'):
        #
        # 
        #
        self.base_path = os.path.abspath(os.path.expanduser(base_path))
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def shoot(self, callback):
        print 'Shooting'

        A = np.random.randint(low=0, high=255, size=(480, 640)).astype(np.uint8)
        
        filename = '{time}_{formated_time}.jpg'.format(
            time=time.time(),
            formated_time=time.strftime("%Y_%m_%d_%H_%M_%S", time.gmtime())
        )
        capture_path = os.path.join(self.base_path, filename)

        img = Image.fromarray(A)
        img.save(capture_path)

        callback(capture_path)
        
