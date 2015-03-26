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
from AUVSIairborne.image_acquisition import ImageAcquirer, AcquisitionController


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Start the airborne server"
                                                 " - Oris' version.")

    parser.add_argument('--port', type=int, default=8844,
                        help='Control port(default=8844).')
    parser.add_argument('--gs_ip', type=str,
                        help='Ground station IP')
    parser.add_argument('--handler_path', type=str,
                        help='path to the image handler file')
    args = parser.parse_args()

    camera_controller = CameraController(CanonCamera())

    image_sending = DirSyncClientFactory(
        dir_to_sync=settings.RESIZED_IMAGES_FOLDER,
        sync_interval=1,
        ftp_user='auvsi',
        ftp_pass='1234'
    )

    def dummy_data(x):
        log.msg("Data retrieved")
        return "DATA!"

    acquirer_controller = AcquisitionController(ImageAcquirer(
        dir_path=settings.IMAGES_FOLDER,
        poll_interval=1,
        image_handler_path=args.handler_path,
        data_retriever=dummy_data)
    )

    control_factory = SystemControlFactory()
    control_factory.subscribe_subsystem("camera", camera_controller.apply_cmd)
    control_factory.subscribe_subsystem("compress",
                                        acquirer_controller.apply_cmd)

    log.startLogging(stdout)
    reactor.listenTCP(args.port, control_factory)
    reactor.connectTCP(args.gs_ip, 21, image_sending)
    reactor.run()
