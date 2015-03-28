""" This module shall watch a given directory to watch for new files,
and send those new files downstream using ftp.
"""
__author__ = 'Ori'


from twisted.internet import task
from twisted.internet.protocol import ReconnectingClientFactory
from twisted.protocols.ftp import FTPClient
from twisted.python import log
from AUVSIairborne.file_scheduler import FileScheduler
import os


def send_file(consumer, path):
    log.msg("send_file({})".format(path))

    with open(path, 'rb') as file:
        for line in file.read():
            consumer.write(line)

    consumer.finish()


def sync_files(ftp_client, scheduler):
    log.msg("Syncing Files")

    #TODO this loop couses the reset_sending to be ineffective
    # starts to send all the files before going back to main loop
    for file in scheduler:
        consumer_defer, control_defer = ftp_client.storeFile(file)
        file_path = os.path.join(scheduler.dir_path, file)
        consumer_defer.addCallback(send_file, path=file_path)


class DirSyncClientFactory(ReconnectingClientFactory):
    protocol = FTPClient
    maxDelay = 32
    factor = 1.15
    initialDelay = 2

    # reactor_ my be extracted to controller
    def __init__(self, dir_to_sync, sync_interval, reactor_,
                 ftp_user='anonymous', ftp_pass='Ori@auvsi.technion'):

        self.dir_to_sync = dir_to_sync
        self.file_scheduler = FileScheduler(dir_to_sync)

        self.sync_interval = sync_interval
        self.sync_task = None

        self.reactor = reactor_

        self.user = ftp_user
        self.password = ftp_pass

        super(type(self), self).__init__()

    def startedConnecting(self, connector):
        log.msg("Trying to connect to ground station"
                "({}) via ftp.".format(connector.host))

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
        if self.sync_task is not None:
            self.sync_task.stop()

    def clientConnectionFailed(self, connector, reason):
        log.msg("connection failed")
        self.retry(connector)
        if self.sync_task is not None:
            self.sync_task.stop()

    def connect(self, ip):
        self.reactor.connectTCP(ip, 21, self)

    def reset_sending(self):
        self.file_scheduler.reset()

if __name__ == "__main__":

    from twisted.internet import reactor
    from sys import stdout
    import argparse

    parser = argparse.ArgumentParser(description='Start directory'
                                                 'synchronization via ftp.')
    parser.add_argument('dir',
                        help='directory to watch')
    parser.add_argument('ip',
                        help="server's ip (ground-station)")
    parser.add_argument('-T', type=float, default=1, dest='sync_interval',
                        help="Time interval for synchronization")
    parser.add_argument('--port', type=int, default=21,
                        help="server's port")
    parser.add_argument('-u', '--user', type=str, default='anonymous',
                        help="login name")
    parser.add_argument('-p', '--pass', type=str, default='auvsi@Technion',
                        help="password", dest='pass_')
    parser.add_argument('-l', '--log', type=str, default=None,
                        help="log file path", dest='log_')
    args = parser.parse_args()

    log_f = stdout if args.log_ is None else open(args.log_, 'w')
    log.startLogging(log_f)

    dir_sync_factory = DirSyncClientFactory(args.dir,
                                            sync_interval=args.sync_interval,
                                            reactor_=reactor,
                                            ftp_user=args.user,
                                            ftp_pass=args.pass_)
    reactor.connectTCP(args.ip, args.port, dir_sync_factory)
    reactor.run()