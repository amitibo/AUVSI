""" This module shall watch a given directory to watch for new files,
and send those new files downstream using ftp.
"""
__author__ = 'Ori'


from twisted.internet import task
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.ftp import FTPClient
from twisted.python import log
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


def send_file(consumer, path):
    log.msg("send_file({})".format(path))

    with open(path, 'rb') as file:
        for line in file.read():
            consumer.write(line)

    consumer.finish()


def sync_files(ftp_client, scheduler):
    log.msg("Syncing Files")

    for file in scheduler:
        consumer_defer, control_defer = ftp_client.storeFile(file)
        file_path = os.path.join(scheduler.dir_path, file)
        consumer_defer.addCallback(send_file, path=file_path)


class DirSyncClientFactory(ReconnectingClientFactory):
    protocol = FTPClient

    def __init__(self, dir_to_sync, sync_interval,
                 ftp_user='anonymous', ftp_pass='Ori@auvsi.technion'):

        self.dir_to_sync = dir_to_sync
        self.file_scheduler = FileSendingScheduler(dir_to_sync)

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

        self.sync_task = task.LoopingCall(sync_files,
                                          ftp_client=ftp_client,
                                          scheduler=self.file_scheduler)
        self.sync_task.start(self.sync_interval)

        return ftp_client

    def clientConnectionLost(self, connector, reason):
        log.msg("connection lost")
        self.retry(connector)
        self.sync_task.stop()

    def clientConnectionFailed(self, connector, reason):
        log.msg("connection failed")
        self.retry(connector)
        self.sync_task.stop()


if __name__ == "__main__":

    import AUVSIairborne.global_settings as settings
    from twisted.internet import reactor
    from sys import stdout
    import argparse

    log.startLogging(stdout)

    # parser = argparse.ArgumentParser(description='Start directory'
    #                                              'synchronization via ftp.')
    # parser.add_argument('dir', required=True,
    #                     help='directory to watch')
    # parser.add_argument('ip', required=True,
    #                     help="server's ip (ground-station)")
    # parser.add_argument('--port', type=int, defult=21,
    #                     help="server's port")
    # parser.add_argument(['-u', '--user'], type=str, defult='anonymous',
    #                     help="login name")
    # parser.add_argument(['-p', '--pass'], type=str, defult='auvsi@Technion',
    #                     help="password")
    # args = parser.parse_args()

    dir_sync_factory = DirSyncClientFactory(r'C:\Users\Ori\ftp_playground',
                                            sync_interval=1,
                                            ftp_user=settings.FTP['user'],
                                            ftp_pass=settings.FTP['pass'])
    reactor.connectTCP('192.168.43.167', 21, dir_sync_factory)
    reactor.run()