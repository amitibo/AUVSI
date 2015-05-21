__author__ = 'User'
import ftplib
import os

client = ftplib.FTP(host='192.168.2.100',
                    user='SRIC',
                    passwd='SRIC',
                    timeout=)

files = client.nlst()
print "Got file list: {}".format(files)

def write_file(data):
    print "Retried data: '{}'".format(data)
    with open(files[1], 'wb') as f:
        f.write(data)

print "Retrieving file: {}".format(files[1])
client.retrbinary("RETR " + files[1], write_file)

file_to_stor = r'C:\Users\User\Documents\auvsi_ftp\resized\?2015_05_21_12_17_00_085985.resized.jpg'
file_to_stor_name = os.path.basename(file_to_stor)

print "Storing file: {}".format(file_to_stor_name)
client.storbinary("STOR " + file_to_stor_name, open(file_to_stor, 'rb'))
print "Storing file completed"

print "Finished SRCIC"

client.quit()
