__author__ = 'Ori'

from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver
from twisted.python import log


class CameraControlProtocol(LineReceiver):
    """
    This is the protocol which the airborne server will use to
    get commands for the camera with.
    """
    def __init__(self, factory, address):
        self.factory = factory
        self.address = address

    def connectionMade(self):
        host = {'ip':self.address.host, 'port':self.address.port}
        if self.factory.is_connection_allowed():
            self.factory.connection_was_made()
            log.msg("Connection made by {ip}:{port}.".format(**host))
        else:
            self.sendLine("Already connected.")
            log.msg("Illegal connection attempt by {ip}:{port},"
                    "someone already connected.".format(**host))
            self.transport.loseConnection()
            return
        self.sendLine("HI!!!")

    def lineReceived(self, line):
        if "s" == line:
            log.msg("got '{}' as data".format(line))
        else:
            log.msg("Unknown command: {}".format(line))


class CameraControlFactory(Factory):
    def __init__(self):
        self.connectionsPool = 1

    def buildProtocol(self, addr):
        return CameraControlProtocol(self, addr)

    def is_connection_allowed(self):
        """
        :return:
        true if a new connection is allowed
        false otherwise
        """
        return self.connectionsPool > 0

    def connection_was_made(self):
        self.connectionsPool -= 1

    def connection_terminated(self):
        self.connectionsPool += 1


if __name__ == "__main__":
    """
    This is a little example for the camera control protocol.
    It can be tested using a simple Telnet client.
    """
    from twisted.internet import reactor
    from sys import stdout

    log.startLogging(stdout)
    reactor.listenTCP(8855, CameraControlFactory())
    reactor.run()