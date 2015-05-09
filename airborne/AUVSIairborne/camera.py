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
import json
import time
import glob
import cv2
import os
import shutil

class BaseCamera(object):
    """Abstract class for a camera, not to be used directly."""

    def __init__(self, zoom=45, shutter=2000, ISO=100, aperture=5):

        self.base_path = gs.IMAGES_FOLDER
        if not os.path.exists(self.base_path):
            os.makedirs(self.base_path)

        self.setParams(zoom=zoom, shutter=shutter, ISO=ISO, aperture=aperture)

    def _getName(self):
        filename = 'ZZ{formated_time}.jpg'.format(
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

        base_path = os.path.join(gs.SIMULATION_DATA, 'images')
        imgs_paths = sorted(glob.glob(os.path.join(base_path, '*.jpg')))
        img_index = 0
        while run.value == 1:
            time.sleep(0.5)
            
            #
            # Pick up an image from disk
            #
            #img = AUVSIcv.Image(imgs_paths[img_index])
            new_name = self._getName()
            print 'Capturing new image: {img_path} to path: {new_path}'.format(img_path=imgs_paths[img_index], new_path=new_name)            
            shutil.copyfile(imgs_paths[img_index], new_name)
            
            img_index += 1
            img_index = img_index % len(imgs_paths)
            
            
            #
            # TODO:
            # I broke here the ability to add targets to images.
            # the reason is that I don't want to lose the exif data
            # in the image. This link http://stackoverflow.com/questions/9808451/how-to-add-custom-metadata-to-opencv-numpy-image
            # might help to solve this.
            #
            #try:
                #data_path = os.path.splitext(imgs_paths[3])[0]+'.txt'            
                #with open(data_path, 'r') as f:
                    #data = json.load(f)
                    
                #img.calculateExtrinsicMatrix(
                    #latitude=data['latitude'],
                    #longitude=data['longitude'],
                    #altitude=data['altitude'],
                    #yaw=data['yaw'],
                    #pitch=data['pitch'],
                    #roll=data['roll'],
                #)
    
                ##
                ## Create a target.
                ##
                #target = AUVSIcv.randomTarget(
                    #altitude=0,
                    #longitude=32.8167,
                    #latitude=34.9833
                #)
                     
                ##
                ## Paste it on the image.
                ##
                #img.paste(target)
            #except:
                #pass
            
            ##
            ## Save the image to disk (should trigger the image processing code).
            ##
            #cv2.imwrite(self._getName(), img.img)

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
        shoot_cmd = """\"remoteshoot {local_folder} -tv=1/{shutter} -sv={ISO} -av={aperture} -cont=9000\"""".format(
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


class CameraController(object):
    def __init__(self, camera):
        self.camera = camera

    def __call__(self, cmd):
        camera = self.camera

        if "start" == cmd:
                camera.startShooting()
                log.msg("Start shooting!")

        elif "stop" == cmd:
            camera.stopShooting()
            log.msg("Stop shooting!")

        elif cmd.startswith("set"):
            #TODO set parameters isn't working for each parameter,
            # check the camera class
            words = cmd.split()
            try:
               params = {words[i]: words[i+1] for i in range(1, len(words), 2)}
            except IndexError as e:
                log.msg("Parameters need to be in pairs <param> <data>: "
                        "'{}'".format(cmd))
                log.err(e)
                return

            camera.setParams(params)
            log.msg("Sets {}".format(str(params)))
