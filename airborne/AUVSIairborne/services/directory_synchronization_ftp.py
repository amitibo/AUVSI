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
    def __init__(self, dir_path, reversed_order=False):
        self.dir_path = dir_path
        self.files_sent = []
        self.files_skipped = []
        self.reverse_order = reversed_order

    def __iter__(self):
        return self

    def next(self):
        result = self._next_file()
        if result is None:
            raise StopIteration()

        return result

    def _next_file(self):
        files = os.listdir(self.dir_path)
        files.sort(reverse=self.reverse_order)

        for file_name in files:
            if self._needs_to_be_sent(file_name):
                self.files_sent.append(file_name)
                return file_name
        return None

    def reset(self):
        skip_files = []
        for file_name in os.listdir(self.dir_path):
            if self._needs_to_be_sent(file_name):
                skip_files.append(file_name)

        log.msg("FileSendingScheduler was reset,"
                "skipping: {}".format(skip_files))

        self.files_skipped.extend(skip_files)

    def _needs_to_be_sent(self, file_name):
        file_was_sent = file_name in self.files_sent
        file_was_skipped = file_name in self.files_skipped
        return (not file_was_sent) and (not file_was_skipped)


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
        if self.sync_task is not None:
            self.sync_task.stop()

    def clientConnectionFailed(self, connector, reason):
        log.msg("connection failed")
        self.retry(connector)
        if self.sync_task is not None:
            self.sync_task.stop()

    def connect(self, reactor, ip):
        raise NotImplementedError()

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
                                            ftp_user=args.user,
                                            ftp_pass=args.pass_)
    reactor.connectTCP(args.ip, args.port, dir_sync_factory)
    reactor.run()