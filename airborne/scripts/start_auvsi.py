from __future__ import division
import argparse
from AUVSIairborne.camera import CameraController, CanonCamera
from AUVSIairborne.services.system_control import SystemControlFactory
from twisted.python import log
from sys import stdout
from twisted.internet import reactor
from AUVSIairborne.services.directory_synchronization_ftp import \
    DirSyncClientFactory
import AUVSIairborne.global_settings as settings

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Start the airborne server"
                                                 " - Oris' version.")

    parser.add_argument('--port', type=int, default=8844,
                        help='Control port(default=8844).')
    parser.add_argument('--gs_ip', type=str,
                        help='Ground station IP')
    args = parser.parse_args()

    camera_controller = CameraController(CanonCamera())

    control_factory = SystemControlFactory()
    control_factory.subscribe_subsystem("camera", camera_controller.apply_cmd)

    image_sending = DirSyncClientFactory(
        dir_to_sync=settings.IMAGES_FOLDER,
        sync_interval=1,
        ftp_user='auvsi',
        ftp_pass='1234'
    )

    log.startLogging(stdout)
    reactor.listenTCP(args.port, control_factory)
    reactor.connectTCP(args.gs_ip, 21, image_sending)
    reactor.run()
