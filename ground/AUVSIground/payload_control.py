__author__ = 'Ori'

from telnetlib import Telnet


class PayloadController(object):
    def __init__(self, payload_ip, payload_control_port=8844,
                 ftp_server_ip=None):
        self._payload_ip = payload_ip
        self._payload_port = payload_control_port
        #TODO: use netifaces to obtain the computer ip as default
        self._ftp_server_ip = ftp_server_ip

        self._telnet = None

        self._delimiter = b'\r\n'

    def connect(self):
        if not self._telnet:
            self._telnet = Telnet(host=self._payload_ip,
                                  port=self._payload_port)

    def _wait_ack(self):
        self._telnet.read_until("More")

    def camera_start(self):
