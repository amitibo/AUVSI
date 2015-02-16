from __future__ import division
import global_settings as gs
import numpy as np
from datetime import datetime
import subprocess as sbp
import signal
import Image
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
    def __init__(self, zoom, *params, **kwds):
        super(CanonCamera, self).__init__(*params, **kwds)

        params = [
            '-c',
            '-erec',
            """-e"
            luar enter_alt();
            call_event_proc('SS.Create');
            call_event_proc('SS.MFOn');
            set_prop(222,0);
            set_focus(65000);
            set_prop(272,0);
            set_prop(105,3);
            set_zoom_speed(1);
            set_zoom({zoom});\"
            """.format(zoom=zoom)
        ]

        cmd = " ".join([gs.CHDKPTP_PATH] + params)
        output = sbp.check_output([cmd], shell=True)
        print output

        self._shooting_proc = None

    def startShooting(self, shutter_speed=50, ISO=50, aperture=4):

        params = [
            "-c",
            "-e\"remoteshoot {local_folder} -tv=1/{shutter_speed} -sv={ISO} -av={aperture} -cont=9000\"".format(
                local_folder=gs.IMAGES_FOLDER,
                shutter_speed=shutter_speed,
                ISO=ISO,
                aperture=aperture
                ),
            "-e\"luar set_lcd_display(0);\""
        ]
        cmd = gs.CHDKPTP_PATH + " " + params[0] + " " + params[1]

        self._shooting_proc = sbp.Popen(
            [cmd],
            shell=True,
            stdout=sbp.PIPE,
            stderr=sbp.PIPE,
            preexec_fn=os.setsid
        )

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
        params = [
            "-c",
            "-e\"killscript;\""
        ]
        cmd = gs.CHDKPTP_PATH + " " + params[0] + " " + params[1]

        output = sbp.check_output([cmd],shell=True)
        print output


