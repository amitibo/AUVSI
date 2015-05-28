__author__ = 'User'
import ftplib
import os
from socket import timeout

target_file = r'2015_05_27_15_20_12_752972.resized.jpg'

retry = True
while retry:
    try:
        client = ftplib.FTP(host='192.168.2.106',
                            user='SRIC',
                            passwd='SRIC',
                            timeout=20)
        retry = False
    except timeout:
        print "Trying to connect"
        retry = True


files = client.nlst()
print "Got file list: {}".format(files)

ret_file = "sric.txt"

def write_file(data):
    print "Retried data: '{}'".format(data)
    with open(ret_file, 'wb') as f:
        f.write(data)

print "Retrieving file: {}".format(ret_file)
client.retrbinary("RETR " + ret_file, write_file)

file_to_stor = os.path.join(r'C:\Users\User\Documents\auvsi_ftp\resized', target_file)
file_to_stor_name = os.path.basename(file_to_stor)

print "Storing file: {}".format(file_to_stor_name)
client.storbinary("STOR " + file_to_stor_name, open(file_to_stor, 'rb'))
print "Storing file completed"

print "Finished SRCIC"

client.quit()
