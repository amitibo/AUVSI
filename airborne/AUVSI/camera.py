from __future__ import division
import global_settings as gs
import numpy as np
from datetime import datetime
import subprocess as sbp
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
    def __init__(self, *params, **kwds):
        super(MockupCamera, self).__init__(*params, **kwds)
    
    def shoot(self, callback):
        print 'Shooting'

        A = np.random.randint(low=0, high=255, size=(480, 640)).astype(np.uint8)
        
        capture_path = self._getName()

        img = Image.fromarray(A)
        img.save(capture_path)

        callback(capture_path)
        

class CanonCamera(BaseCamera):
    def __init__(self, zoom, *params, **kwds):
        super(MockupCamera, self).__init__(*params, **kwds)

        params = ["-c", "-erec", "-e\"luar enter_alt(); call_event_proc('SS.Create'); call_event_proc('SS.MFOn'); set_prop(222,0); set_focus(65000); set_prop(272,0); set_prop(105,3); set_zoom_speed(1); set_zoom({});\"".format(zoom)]
        try:
            cmd = chdkptp + " " + params[0] + " " + params[1] + " " + params[2]
            logger.info(cmd)
            output = subprocess.check_output([cmd], shell=True)
            print output
            logger.info("init: {}".format(output))
            if output.find("ERROR") >= 0 and output.find('already in rec') == -1:
                logger.error("Camera error:\n{}".format(output))
                return False
            return True
    
        except Exception as e:
            logger.error("Unable to run camera init command!\n{}".format(e), exc_info=True)
            return False
        

