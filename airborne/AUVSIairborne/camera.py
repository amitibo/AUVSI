from __future__ import division
import global_settings as gs
import numpy as np
from datetime import datetime
import subprocess as sbp
import multiprocessing as mp
import AUVSIcv
import signal
import Image
import glob
import time
import cv2
import os


class BaseCamera(object):
    """Abstract class for a camera, not to be used directly."""
    
    def __init__(self, zoom=45, shutter=1600, ISO=100, aperture=4):
        self.zoom = zoom
        self.shutter = shutter
        self.ISO = ISO
        self.aperture = aperture

        self.base_path = gs.IMAGES_FOLDER
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

    def _getName(self):
        filename = '{formated_time}.jpg'.format(
            formated_time=datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        )
        return os.path.join(self.base_path, filename)


class SimulationCamera(BaseCamera):
    def __init__(self, *params, **kwds):
        super(SimulationCamera, self).__init__(*params, **kwds)

        self._shooting_proc = None

    def _shootingLoop(self, run):
        """Inifinite shooting loop. To run on separate process."""
        
        base_path = os.environ['AUVSI_CV_DATA']
        imgs_paths = glob.glob(os.path.join(base_path, '*.jpg'))
        img_index = 0
        while run.value == 1:

            #
            # Pick up an image from disk
            #
            img = AUVSIcv.Image(imgs_paths[img_index])
            img_index += 1
            img_index = img_index % len(imgs_paths)
            
            #
            # Create a target.
            #
            target = AUVSIcv.StarTarget(
                n=6,
                size=2,
                orientation=30,
                altitude=0,
                longitude=32.8167+0.0001,
                latitude=34.9833+0.00001, 
                color=(70, 150, 100), 
                letter='A', 
                font_color=(140, 230, 240)
            )

            #
            # Paste it on the image.
            #
            img.paste(target)
            
            #
            # Save the image to disk (should trigger the image processing code).
            #
            cv2.imwrite(self._getName(), img.img)
            
    def startShooting(self):
        self._run_flag = mp.Value('i', 1)
        self._shooting_proc = mp.Process(target=self._shootingLoop, args=(self._run_flag, ))
        self._shooting_proc.start()
        
    def stopShooting(self):
        if self._shooting_proc is None:
            return
        
        #
        # Stop the loop
        #
        self._run_flag.value = 0
        self._shooting_proc.join()


class CanonCamera(BaseCamera):
    def __init__(self, *params, **kwds):
        super(CanonCamera, self).__init__(*params, **kwds)

        rec_cmd = 'rec'
        self._blocking_cmd(rec_cmd)

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
        result = sbp.call(
            " ".join([gs.CHDKPTP_PATH, '-c', '-e'+cmd]),
            shell=True
        )
        return result

    def _nonblocking_cmd(self, cmd):
        p = sbp.Popen(
            " ".join([gs.CHDKPTP_PATH, '-c', '-e'+cmd]),
            shell=True,
            stdout=sbp.PIPE,
            stderr=sbp.PIPE,
            preexec_fn=os.setsid
        )
        
        return p
    
    def startShooting(self):

        zoom_cmd = """\"luar set_zoom({zoom});\"""".format(zoom=self.zoom)
        self._blocking_cmd(zoom_cmd)

        shoot_cmd = """\"remoteshoot {local_folder} -tv=1/{shutter} -sv={ISO} -av={aperture} -cont=9000\"""".format(
            local_folder=gs.IMAGES_FOLDER,
            shutter=self.shutter,
            ISO=self.ISO,
            aperture=self.aperture
        )

        self._shooting_proc = self._nonblocking_cmd(shoot_cmd)

    def stopShooting(self):

        if self._shooting_proc is None:
            return

        os.killpg(self._shooting_proc.pid, signal.SIGINT)
