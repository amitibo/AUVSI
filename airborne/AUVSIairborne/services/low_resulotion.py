__author__ = 'Ori'
"""
This module shall watch a given directory for new files,
and send those new files downstream.
"""

from twisted.internet import task
from twisted.internet.protocol import ReconnectingClientFactory, ClientFactory
from twisted.protocols.ftp import FTPClient
from twisted.python import log
import AUVSIairborne.global_settings as settings
import os


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
    log.msg("sync_images")

    for image in scheduler:
        consumer_defer, control_defer = ftp_client.storeFile(image)
        image_path = os.path.join(scheduler.dir_path, image)
        consumer_defer.addCallback(send_image, path=image_path)


class DirSyncClientFactory(ReconnectingClientFactory):
    protocol = FTPClient

    def __init__(self, dir_to_sync, sync_interval,
                 ftp_user='anonymous', ftp_pass='Ori@auvsi.technion'):

        self.dir_to_sync = dir_to_sync
        self.image_scheduler = FileSendingScheduler(dir_to_sync)

        self.sync_interval = sync_interval
        self.sync_task = None

        self.user = ftp_user
        self.password = ftp_pass

        super(type(self), self).__init__()

    def startedConnecting(self, connector):
        log.msg("Trying to connect to ground station via ftp.")

    def buildProtocol(self, addr):
        log.msg("TCP connected successfully, awaits ftp authorization.")

        self.resetDelay()

        ftp_client = FTPClient(username=self.user, password=self.password)

        self.sync_task = task.LoopingCall(sync_images,
                                          ftp_client=ftp_client,
                                          scheduler=self.image_scheduler)
        self.sync_task.start(self.sync_interval)

        return ftp_client

    def clientConnectionLost(self, connector, reason):
        log.msg("connection lost")
        self.retry(connector)
        self.sync_task.stop()

    def clientConnectionFailed(self, connector, reason):
        log.msg("connection failed")


if __name__ == "__main__":
    from twisted.internet import reactor
    from sys import stdout

    log.startLogging(stdout)

    dir_sync_factory = DirSyncClientFactory(r'C:\Users\Ori\Pictures',
                                            sync_interval=1,
                                            ftp_user=settings.FTP['user'],
                                            ftp_pass=settings.FTP['pass'])
    reactor.connectTCP('localhost', 21, dir_sync_factory)
    reactor.run()