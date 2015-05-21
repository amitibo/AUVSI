__author__ = 'User'
import telnetlib

tel = telnetlib.Telnet(host="192.168.1.101",
                       port=8855)
delimiter = b'\r\n'
cmd_list = ("resize_download connect ip 192.168.1.100",
            "data_download connect ip 192.168.1.100",
            "camera set shutter 2500 aperture 3 ISO 100")

for cmd in cmd_list:
    tel.write(cmd + delimiter)
    tel.read_until("More")
