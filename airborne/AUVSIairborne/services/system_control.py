""" This module gives a control line to the aerial pc.
Subsystems may subscribe to the SystemControlFactory in
order to be controlled through the ground-station.
It is intended to work in pair the ground station gui.
In case of problem, can be accessed through telnet.
"""
__author__ = 'Ori'

from twisted.internet.error import ConnectionDone
from twisted.internet.protocol import Factory, Protocol
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from AUVSIairborne import UnknownCommand


class SystemControlProtocol(LineReceiver):
    """ This is the protocol which the airborne server will use to
    get commands for the system with.
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
            subsystem_id, cmd = line.split(' ', 1)
        except ValueError as e:
            log.msg("Wrong format: '{}'".format(line))
            log.err(e)
            self.sendLine("More master?")
            return

        try:
            self.factory.subsystems[subsystem_id](cmd)
        except IndexError as e:
            log.msg("Unknown subsystem: '{}'".format(subsystem_id))
            log.err(e)

        self.sendLine("More master?")

    def connectionLost(self, reason=ConnectionDone()):
        log.msg("Connection was Lost: '{}".format(str(reason)))

        self.factory.connection_terminated()
        Protocol.connectionLost(self, reason)


class SystemControlFactory(Factory):
    def __init__(self):
        self.connectionsPool = 1
        self.subsystems = {}

    def buildProtocol(self, addr):
        return SystemControlProtocol(self, addr)

    def subscribe_subsystem(self, subsystem_id, subsystem_handler):

        assert callable(subsystem_handler)

        if subsystem_id in self.subsystems:
            raise ValueError("Subsystem id already exists.")

        self.subsystems[subsystem_id] = subsystem_handler

    def is_connection_allowed(self):
        """:return:
        true if a new connection is allowed
        false otherwise
        """
        return self.connectionsPool > 0

    def connection_was_made(self):
        self.connectionsPool -= 1

    def connection_terminated(self):
        self.connectionsPool += 1


class ReflectionController(object):
    """ This class uses reflection to implement an easy
    generic control interface to any object.
    """
    def __init__(self, controlled_obj):
        self.controlled_obj = controlled_obj

    def _str_params_to_dic(self, params_str):
        if params_str is None:
            return {}

        params_words = params_str.split()
        try:
            params_dic = {params_words[i]: params_words[i + 1] for i
                          in range(0, len(params_words), 2)}
        except IndexError:
            raise UnknownCommand("Can't extract parameters from {params}"
                                 "Parameters should come in pairs e.g."
                                 " 'a 3 b 7...'".format(params=params_str))

        return params_dic

    def apply_cmd(self, cmd):
        try:
            method_name, params_str = cmd.split(' ', 1)
        except ValueError:
            method_name = cmd
            params_str = None

        params_dic = self._str_params_to_dic(params_str)

        try:
            method = getattr(self.controlled_obj, method_name)
        except AttributeError:
            raise UnknownCommand(str(type(self.controlled_obj)) +
                                 " could not do: " + str(cmd))

        return method(**params_dic)


if __name__ == "__main__":
    """
    This is a little example for the camera control protocol.
    It can be tested using a simple Telnet client.
    """
    from twisted.internet import reactor
    from sys import stdout
    from AUVSIairborne.camera import SimulationCamera, CameraController

    def dummy_shout(string):
        """ Stub subsystem  """
        print string

    camera_controller = CameraController(SimulationCamera())

    control_factory = SystemControlFactory()
    control_factory.subscribe_subsystem("camera", camera_controller.apply_cmd)
    control_factory.subscribe_subsystem("dummy_shout", dummy_shout)

    log.startLogging(stdout)
    reactor.listenTCP(8844, control_factory)
    reactor.run()