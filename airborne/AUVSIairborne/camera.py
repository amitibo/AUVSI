from __future__ import division
import global_settings as gs
from datetime import datetime
from twisted.python import log
try:
    import subprocess32 as sbp
except ImportError:
    import subprocess as sbp
import multiprocessing as mp
import AUVSIcv
import signal
import shlex
import time
import glob
import cv2
import os


class BaseCamera(object):
    """Abstract class for a camera, not to be used directly."""
    
    def __init__(self, zoom=45, shutter=1600, ISO=100, aperture=4):

        self.base_path = gs.IMAGES_FOLDER
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        self.setParams(zoom=zoom, shutter=shutter, ISO=ISO, aperture=aperture)

    def _getName(self):
        filename = '{formated_time}.jpg'.format(
            formated_time=datetime.now().strftime("%Y_%m_%d_%H_%M_%S_%f")
        )
        return os.path.join(self.base_path, filename)

    def setParams(self, zoom, shutter, ISO, aperture, **kwds):
        self.zoom = zoom
        self.shutter = shutter
        self.ISO = ISO
        self.aperture = aperture


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



def kill(proc_pid):
    """
    Recursively kill a processes and all its children.
    Taken from: http://stackoverflow.com/questions/4789837/how-to-terminate-a-python-subprocess-launched-with-shell-true/4791612#4791612
    """

    import psutil

    process = psutil.Process(proc_pid)

    for proc in process.get_children(recursive=True):
        proc.kill()

    process.kill()


class CanonCamera(BaseCamera):
    def __init__(self, *params, **kwds):

        rec_cmd = 'rec'
        init_cmd = """\"luar enter_alt();
            call_event_proc('SS.Create');
            call_event_proc('SS.MFOn');
            set_prop(222,0);
            set_focus(65000);
            set_prop(272,0);
            set_prop(105,3);
            set_zoom_speed(1);
            set_lcd_display(0);\""""

        self._blocking_cmds(rec_cmd, init_cmd)
        self._shooting_proc = None
        self._set_zoom = True

        super(CanonCamera, self).__init__(*params, **kwds)

    def _nonblocking_cmds(self, *cmds):

        full_cmd = " ".join([gs.CHDKPTP_PATH, '-c'] + ['-e'+cmd for cmd in cmds] + ['-e"q"'])
        log.msg('Executing cmd: {cmd}'.format(cmd=full_cmd))

        p = sbp.Popen(
            shlex.split(full_cmd)
        )
        return p

    def _blocking_cmds(self, *cmds):

        full_cmd = " ".join([gs.CHDKPTP_PATH, '-c'] + ['-e'+cmd for cmd in cmds] + ['-e"q"'])
        log.msg('Executing cmd: {cmd}'.format(cmd=full_cmd))

        result = sbp.call(
            full_cmd,
            shell=True
        )
        return result

    def setParams(self, **kwds):

	super(CanonCamera, self).setParams(**kwds)

	if 'zoom' in kwds and self._set_zoom:
            zoom_cmd = """\"luar set_zoom({zoom})\"""".format(zoom=self.zoom)
            self._blocking_cmds(zoom_cmd)
            self._set_zoom = False

    def startShooting(self):
        shoot_cmd = """\"remoteshoot {local_folder} -tv=1/{shutter} -sv={ISO} -av={aperture} -cont=1000\"""".format(
            local_folder=gs.IMAGES_FOLDER,
            shutter=self.shutter,
            ISO=self.ISO,
            aperture=self.aperture
        )

        self._shooting_proc = self._nonblocking_cmds(shoot_cmd)

    def stopShooting(self):

        if self._shooting_proc is None:
            return

        kill(self._shooting_proc.pid)
        self._shooting_proc = None
        
        self._blocking_cmds('killscript')
