__author__ = 'Ori'
from telnetlib import Telnet
from socket import error as SocketError
from kivy.logger import Logger
import threading


class AirborneUnavailable(Exception):
    pass


class AirborneError(Exception):
    pass


class Payload(object):
    LOGGER_PREFIX = "Payload Controller"

    def __init__(self, ip, port=8855):
        self.ip = ip
        self.port = port

        self._telnet_client = None
        self._delimiter = b'\r\n'

        self._is_camera_on = False

    @staticmethod
    def _log_debug(msg):
        Logger.debug("{prefix}: {msg}".format(prefix=Payload.LOGGER_PREFIX,
                                             msg=msg))

    @staticmethod
    def _log_info(msg):
        Logger.debug("{prefix}: {msg}".format(prefix=Payload.LOGGER_PREFIX,
                                             msg=msg))

    def disconnect(self):
        try:
            self._telnet_client.close()
        except AttributeError:
            pass
        finally:
            self._telnet_client = None

    def connect(self):
        self.disconnect()
        try:
            self._telnet_client = Telnet(self.ip, self.port)
            Payload._log_info("Connected the airborne's payload")
        except SocketError:
            err_msg = "Failed connecting the airborne's payload"
            Payload._log_info(err_msg)
            raise AirborneUnavailable(err_msg)

        # read all of the welcome massage
        self._telnet_client.read_until(']' + self._delimiter)

        return self

    def _send_cmd_blocking(self, cmd):
        Payload._log_debug("Trying to send to airborne: '{}'".format(cmd))

        client = self._telnet_client
        try:
            client.write(cmd + self._delimiter)
            Payload._log_info("Successfully sent to airborne: '{}'".format(cmd))
        except (AttributeError, SocketError):
            err_msg = "Disconnected from airborne," \
                      "couldn't send: '{}'".format(cmd)
            Payload._log_debug(err_msg)
            raise AirborneUnavailable(err_msg)

        self._process_response()

    def _process_response(self):
        ready_for_next_cmd = "More master?"
        Payload._log_debug("Started processing the airborne system response.")

        client = self._telnet_client

        response = client.read_until(ready_for_next_cmd)
        response = response.strip()
        Payload._log_debug("Server response: '{}'".format(response))
        if response == ready_for_next_cmd:
            return

        # First line of response is the err massage
        err_msg = response.split(self._delimiter, 1)[0]
        raise AirborneError(err_msg)

    def _send_cmd(self, cmd):
        # TODO: Make non non-blocking
        self._send_cmd_blocking(cmd)

    def camera_start(self):
        cmd = "camera start"
        self._send_cmd(cmd)
        self._is_camera_on = True

    def camera_stop(self):
        cmd = "camera stop"
        self._send_cmd(cmd)
        self._is_camera_on = False

    def camera_toggle(self):
        if self._is_camera_on:
            self.camera_stop()
        else:
            self.camera_start()

    def camera_set(self, **kwargs):
        params_tuple = ("{k} {v}".format(k=k, v=kwargs[k]) for k in kwargs)
        params_str = " ".join(params_tuple)

        cmd = "camera set {params}".format(params=params_str)
        self._send_cmd(cmd)

    def download_start(self, dest_ip):
        cmds_template = ("resize_download connect ip {}",
                         "data_download connect ip {}",
                         "crops_download connect ip {}")
        cmds = (cmd.format(dest_ip) for cmd in cmds_template)

        for cmd in cmds:
            self._send_cmd(cmd)

    def crop(self, timestamp, x_range, y_range):
        """
        download a crop of the image.
        The rectangle described by x_range and y_range should be given in the
        full regulation picture coordinate (pixels).

        :param timestamp: the timestamp of the desired crop
        :param x_range: a tuple of (x1, x2)
        :param y_range: a tuple of (y1, y2)
        :return:
        """
        cmd = "crop {timestamp} {x_max} {x_min} {y_max} {y_min}".format(
            timestamp=timestamp,
            x_max=max(x_range), x_min=min(x_range),
            y_max=max(y_range), y_min=min(y_range)
        )
        self._send_cmd(cmd)


if __name__ == "__main__":
    # Logger.setLevel(1)
    payload = Payload('localhost')
    payload.connect()
    # payload.download_start('localhost')
    cam_param = {'ISO': 100, 'shutter': 2500}
    payload.camera_set(**cam_param)

    payload.crop('2015_05_22_18_14_43_351000', (500, 0), (500, 0))

    try:
        payload._send_cmd_blocking("camera w ISO 100")
    except AirborneError as e:
        print str(e)
