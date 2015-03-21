__author__ = 'Ori'
"""
This module shall watch a given directory for new files,
and send those new files downstream.
"""

from twisted.internet import task
from twisted.protocols.ftp import FTPClient, FTPFileListProtocol


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


def send_image(consumer):
    with open(r'C:\Users\Ori\Pictures\hot-girls.jpg', 'rb') as image:
        for line in image.read():
            consumer.write(line)
    consumer.finish()


def sync_images(ftp_client):
    ftp_client.pwd().addCallbacks(success, fail)

    consumer_defer, control_defer = ftp_client.storeFile('coolImage.jpg')
    consumer_defer.addCallbacks(send_image, fail)


if __name__ == "__main__":
    from twisted.internet import reactor
    from twisted.internet.protocol import ClientCreator

    # def dummy():
    #     print "HODOR!!!"
    #
    # task.LoopingCall(dummy).start(0.5)

    creator = ClientCreator(reactor, FTPClient, 'Auvsi',
                            '1234', passive=0)
    creator.connectTCP('localhost', 21).addCallbacks(sync_images, fail)
    reactor.run()