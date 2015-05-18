""" This module contains functions and classes to handle the
images which arrives from the camera (adding metadata, creation of low res
image etc).
"""
__author__ = 'Ori'

from twisted.internet import task, defer
from twisted.python import log
from AUVSIairborne.file_scheduler import FileScheduler
from subprocess import Popen
import os


class ImageAcquirer(object):
    """ Acquires images from a given folder and sends them to the airborne
    image processing pipeline
    """

    def __init__(self, dir_path, poll_interval,
                 image_handler_path, data_retriever):
        """
        :param dir_path: directory to watch
        :param poll_interval: poll interval in seconds
        :param image_handler_path: a python script which will be executed as:
                            "python <image_path>"
        :param image_handler: a function which will be called at the moment
                              the image was found by the ImageAcquirer to
                              retrieve the image metadata
        """

        if not os.path.isfile(image_handler_path):
            raise ValueError("Image handler is not a file")
        if not callable(data_retriever):
            raise ValueError("Data retriever is not callable")

        self.file_scheduler = FileScheduler(dir_path)
        self.poll_interval = poll_interval

        self.image_handler_path = image_handler_path
        self.data_retriever = data_retriever
        self.poll_task = None

    def start(self):
        log.msg("Starts polling images from: {}"
                .format(self.file_scheduler.dir_path))
        if self.poll_task is None:
            self.poll_task = task.LoopingCall(self._poll)

        self.poll_task.start(self.poll_interval)

    def stop(self):
        log.msg("Stops polling images from: {}"
                .format(self.file_scheduler.dir_path))
        self.poll_task.stop()

    def _poll(self):
        #TODO add inotify support for linux system
        image_defer_list = []

        for file_name in self.file_scheduler:
            image_defer = self._generate_pipeline(file_name)
            image_defer.callback(file_name)
            image_defer_list.append(image_defer)
            log.msg("Polled new files: {}".format(file_name))

        return image_defer_list

    def _acquire_data(self, image_name):
        """ Has to be a fast action - runs on mainloop thread """
        #STUB
        #TODO implement

#        meta_data = self.data_retriever(image_name)

        log.msg("Acquired data for image '{}'".format(image_name))

        # image_path = os.path.join(self.dir_path, image_path)

        data_path = ""
        return data_path

    def _generate_pipeline(self, image_name):
        image_path = os.path.join(self.file_scheduler.dir_path, image_name)

        d = defer.Deferred()
        d.addCallback(self._acquire_data)

        def handle_image(data_path):
            #TODO edit Popen settings (stdout...)
            log.msg("Starts new process for image: {}".format(image_name))
            return Popen(["python", self.image_handler_path,
                          image_path, data_path])

        d.addCallback(handle_image)
        d.addErrback(log.err)

        return d




if __name__ == "__main__":
    from sys import stdout
    from time import sleep
    from twisted.internet import reactor

    def dummy_image_handler(air_image):
        log.msg("Handles image: '{}'".format(air_image.path['original']))
        sleep(4)

    def dummy_data_retriever():
        return "DATA!!"

    handler_script = r'C:\Users\Ori\PycharmProjects\auvsi\airborne'
    handler_script += r'\AUVSIairborne\image_handler.py'

    acquirer = ImageAcquirer(dir_path=r'C:\Users\Ori\Pictures',
                             poll_interval=2,
                             image_handler_path=handler_script,
                             data_retriever=dummy_data_retriever)
    log.startLogging(stdout)
    acquirer.start()

    reactor.run()
