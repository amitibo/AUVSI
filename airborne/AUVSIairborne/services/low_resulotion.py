__author__ = 'Ori'
"""
This module shall watch a given directory for new files,
and send those new files downstream.
"""

from twisted.internet import task
from twisted.protocols.ftp import FTPClient
from twisted.python import log
import AUVSIairborne.global_settings as settings
import os


def success(response):
    print 'Success!  Got response:'
    print '---'
    if response is None:
        print None
    else:
        print response
    print '---'


def fail(error):
    print 'Failed.  Error was:'
    print error


class FileSendingScheduler(object):
    def __init__(self, dir_path):
        self.dir_path = dir_path
        self.files_sent = []

    def __iter__(self):
        return self

    def next(self):
        result = self.next_file()
        if result is None:
            raise StopIteration()

        return result

    def next_file(self):
        for file_name in os.listdir(self.dir_path):
            if file_name not in self.files_sent:
                self.files_sent.append(file_name)
                return file_name
        return None


def send_image(consumer, path):
    log.msg("send_image({})".format(path))
    with open(path, 'rb') as image:
        for line in image.read():
            consumer.write(line)
    consumer.finish()


def sync_images(ftp_client, scheduler):
    log.msg("sync_mages")
    for image in scheduler:
        consumer_defer, control_defer = ftp_client.storeFile(image)
        image_path = os.path.join(scheduler.dir_path, image)
        consumer_defer.addCallback(send_image, path=image_path)


def start_sync(ftp_client, scheduler):
    log.msg("Starting sync")
    sync_task = task.LoopingCall(sync_images, ftp_client=ftp_client,
                                 scheduler=scheduler)
    sync_task.start(1)



if __name__ == "__main__":
    from twisted.internet import reactor
    from twisted.internet.protocol import ClientCreator
    from sys import stdout

    log.startLogging(stdout)

    image_scheduler = FileSendingScheduler(r'C:\Users\Ori\Pictures')

    creator = ClientCreator(reactor, FTPClient, 'Auvsi',
                            '1234', passive=0)

    connected = creator.connectTCP('localhost', 21)

    connected.addCallback(start_sync, scheduler=image_scheduler)
    reactor.run()