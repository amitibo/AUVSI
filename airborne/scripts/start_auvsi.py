from __future__ import division
import argparse
from AUVSIairborne.camera import CameraController, CanonCamera, SimulationCamera
from AUVSIairborne.services.system_control import SystemControlFactory
from twisted.python import log
from sys import stdout
from twisted.internet import reactor
from AUVSIairborne.services.directory_synchronization_ftp import \
    DirSyncClientFactory
from AUVSIairborne.image_acquisition import ImageAcquirer
from AUVSIairborne.services.system_control import ReflectionController
from AUVSIairborne import global_settings
from AUVSIairborne.PixHawk import initPixHawkSimulation
from AUVSIairborne.services.crop import CropImageController


def pixhawk_data_retriever(image_name):
    import re
    import json
    import os
    from AUVSIairborne.global_settings import IMAGES_DATA
    from AUVSIairborne.PixHawk import queryPHdata

    date_regex = "[0-9]+_[0-9]+_[0-9]+_[0-9]+_[0-9]+_[0-9]+_[0-9]+"
    time = re.search(date_regex, image_name).group()

    with open(os.path.join(IMAGES_DATA, time + ".json"), 'wb') as data_file:
        json.dump(queryPHdata(time), data_file)
        log.msg("New data file: " + data_file.name)


def parse_commandline_args():
    global parser, args
    parser = argparse.ArgumentParser(description="Start the airborne server"
                                                 " - Oris' version.")
    parser.add_argument('--port', type=int, default=8844,
                        help='Control port(default=8844).')
    parser.add_argument('--camera', type=str, default="cannon",
                        help="The camera to use: cannon(default), simulation")
    parser.add_argument('--handler_path', type=str,
                        help='path to the image handler file')
    return parser.parse_args()


if __name__ == '__main__':

    args = parse_commandline_args()

    camera = None
    if args.camera == "cannon":
        camera = CanonCamera()
    elif args.camera == "simulation":
        camera = SimulationCamera()

    camera_controller = CameraController(camera)

    image_sending_controller = ReflectionController(DirSyncClientFactory(
        dir_to_sync=global_settings.RESIZED_IMAGES_FOLDER,
        dest_dir="resized",
        sync_interval=1,
        reactor_=reactor,
        ftp_user=global_settings.FTP_CREDENTIAL['user'],
        ftp_pass=global_settings.FTP_CREDENTIAL['pass']))

    data_sending_controller = ReflectionController(DirSyncClientFactory(
        dir_to_sync=global_settings.IMAGES_DATA,
        dest_dir="images_data",
        sync_interval=1,
        reactor_=reactor,
        ftp_user=global_settings.FTP_CREDENTIAL['user'],
        ftp_pass=global_settings.FTP_CREDENTIAL['pass']))

    crop_sending_controller = ReflectionController(DirSyncClientFactory(
        dir_to_sync=global_settings.CROPS_FOLDER,
        dest_dir="crops",
        sync_interval=1,
        reactor_=reactor,
        ftp_user=global_settings.FTP_CREDENTIAL['user'],
        ftp_pass=global_settings.FTP_CREDENTIAL['pass']))

    acquirer = ImageAcquirer(
        dir_path= global_settings.IMAGES_FOLDER,
        poll_interval=1,
        image_handler_path=args.handler_path,
        data_retriever=pixhawk_data_retriever)

    crop_controller = CropImageController(
        images_folder=global_settings.IMAGES_RENAMED,
        crops_folder=global_settings.CROPS_FOLDER)

    control_factory = SystemControlFactory()
    control_factory.subscribe_subsystem("camera", camera_controller)

    control_factory.subscribe_subsystem("resize_download",
                                        image_sending_controller)
    control_factory.subscribe_subsystem("data_download",
                                        data_sending_controller)
    control_factory.subscribe_subsystem("crops_download",
                                        crop_sending_controller)
    control_factory.subscribe_subsystem("crop", crop_controller)


    log.startLogging(stdout)

    image_sending_controller.controlled_obj.connect(ip='localhost')
    data_sending_controller.controlled_obj.connect(ip='localhost')
    crop_sending_controller.controlled_obj.connect(ip='localhost')

    acquirer.start()
    initPixHawkSimulation()

    reactor.listenTCP(args.port, control_factory)
    reactor.run()
