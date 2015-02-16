from __future__ import division
import global_settings as gs
import numpy as np
from datetime import datetime
import subprocess as sbp
import signal
import Image
import os


class BaseCamera(object):
    zoom = 45
    shutter = 5000
    ISO = 50
    aperture = 4

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

        A = np.random.randint(
            low=0,
            high=255,
            size=(480, 640)).astype(np.uint8
            )

        capture_path = self._getName()

        img = Image.fromarray(A)
        img.save(capture_path)

        callback(capture_path)


class CanonCamera(BaseCamera):
    def __init__(self, *params, **kwds):
        super(CanonCamera, self).__init__(*params, **kwds)

        init_cmd = """\"luar enter_alt();
            call_event_proc('SS.Create');
            call_event_proc('SS.MFOn');
            set_prop(222,0);
            set_focus(65000);
            set_prop(272,0);
            set_prop(105,3);
            set_zoom_speed(1);
            set_lcd_display(0);\""""

        self._blocking_cmd(init_cmd)
        self._shooting_proc = None

    def _blocking_cmd(self, cmd):
        result = sbp.call([gs.CHDKPTP_PATH, '-c', '-e'+cmd], shell=True)
        return result
    
    def _nonblocking_cmd(self, cmd):
        p = sbp.Popen(
            [gs.CHDKPTP_PATH, '-c', '-e'+cmd],
            shell=True,
            stdout=sbp.PIPE,
            stderr=sbp.PIPE,
            preexec_fn=os.setsid
        )
        
        return p
    
    def startShooting(self):

        zoom_cmd = """\"luar set_zoom({zoom});\"""".format(zoom=self.zoom)
        self._blocking_cmd(zoom_cmd)
        
        shoot_cmd = """\"remoteshoot {local_folder} -tv=1/{shutter_speed} -sv={ISO} -av={aperture} -cont=9000\"""".format(
                local_folder=gs.IMAGES_FOLDER,
                shutter_speed=self.shutter_speed,
                ISO=self.ISO,
                aperture=self.aperture
                )
        
        self._shooting_proc = self._nonblocking_cmd(shoot_cmd)
        
    def stopShooting(self):

        if self._shooting_proc is None:
            return

        #
        # First kill the process
        #
        os.killpg(self._shooting_proc.pid, signal.SIGTERM)

        #
        # Then kill script (needed?)
        #
        kill_cmd = """\"killscript;\""""
        
        self._blocking_cmd(kill_cmd)

