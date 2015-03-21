__author__ = 'Ori'

from twisted.internet.error import ConnectionDone
from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import LineReceiver
from twisted.python import log


class SystemControlProtocol(LineReceiver):
    """
    This is the protocol which the airborne server will use to
    get commands for the camera with.
    """
    def __init__(self, factory, address):
        self.factory = factory
        self.address = address

    def connectionMade(self):
        host = {'ip': self.address.host, 'port': self.address.port}
        if self.factory.is_connection_allowed():
            self.factory.connection_was_made()
            log.msg("Connection made by {ip}:{port}.".format(**host))
        else:
            self.sendLine("Already connected.")
            log.msg("Illegal connection attempt by {ip}:{port},"
                    "someone already connected.".format(**host))
            self.transport.loseConnection()
            return
        self.sendLine("Welcome to camera control channel.")

    def lineReceived(self, line):
        line = str.join(" ", line.split())

        log.msg("Recived: '{}'".format(line))

        try:
            cmd = line.split(' ', 1)[1]
        except IndexError as e:
            log.msg("Wrong format: '{}'".format(line))
            log.err(e)
            self.sendLine("More master?")
            return

        if line.startswith("camera"):
            self.camera_control(cmd)

        elif line.startswith("system"):
            pass

        else:
            log.msg("Unknown system: '{}'".format(line))

        self.sendLine("More master?")

    def connectionLost(self, reason=ConnectionDone()):
        log.msg("Connection was Lost: '{}".format(str(reason)))

        self.factory.connection_terminated()
        Protocol.connectionLost(self, reason)

    def camera_control(self, cmd):
        camera = self.factory.camera

        if "start" == cmd:
                camera.startShooting()
                log.msg("Start shooting!")

        elif "stop" == cmd:
            camera.stopShooting()
            log.msg("Stop shooting!")

        elif cmd.startswith("set"):
            #TODO set parameters isn't working, check the camera class
            words = cmd.split()
            try:
               params = {words[i]: words[i+1] for i in range(1, len(words), 2)}
            except IndexError as e:
                log.msg("Parameters need to be in pairs <param> <data>: "
                        "'{}'".format(cmd))
                log.err(e)
                return

            camera.setParams(params)
            log.msg("Sets {}".format(str(params)))


class SystemControlFactory(Factory):
    def __init__(self, camera):
        self.connectionsPool = 1
        self.camera = camera

    def buildProtocol(self, addr):
        return SystemControlProtocol(self, addr)

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
    from AUVSIairborne.camera import SimulationCamera

    log.startLogging(stdout)
    reactor.listenTCP(8844, SystemControlFactory(SimulationCamera()))
    reactor.run()