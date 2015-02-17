#!/usr/bin/python
import os
import re
import serial
import binascii
from threading import Thread
import MySQLdb
import datetime
import subprocess
import time
import os
import glob
import auvsiDB

def setTime(week, weeksec):
    week = int(week)
    weeksec = float(weeksec)
    if week < 1790: return False
    curdate = datetime.datetime(1980, 1,6) + datetime.timedelta(0,60*60*24*7*week + weeksec)
    os.system('hwclock --set --date \'%s\'' % curdate)
    os.system('hwclock -s')
    print "Set system time to:{}".format(curdate)
    return True

class INS():
        def __init__(self, location, baud_rate, timeout):
                '''
                Initiates variables.

                Keyword arguments:
                location -- the location of the serial connection
                baud_rate -- the baud rate of the connection
                timeout -- the timeout of the connection

                '''
                self.exit = False
                self.location = location
                self.baud_rate = baud_rate
                self.timeout = timeout
                self.serial_dev = None
                self.serial_data = None
                self.clockFlag = False
                
                self.ttime = time.time()
                #Ready the INS variables
                self.data_ins = {'time': float(0.0), 'week': float(0.0), 'head': float(0.0), 'pitch': float(0.0), 'roll': float(0.0), 'lat': float(0.0), 'long': float(0.0), 'alt': float(0.0), 'status': 'A'}
                self.db = MySQLdb.connect(host = auvsiDB.host, user = auvsiDB.user, passwd = auvsiDB.passwd, db = auvsiDB.db)
                self.cur = self.db.cursor()
        
        
        def start(self):
                '''
                Creates a thread to read serial connection data.
                '''
                try:
                    self.serial_dev = serial.Serial(self.location, self.baud_rate, self.timeout)
                    serial_thread = Thread(None,self.read_thread,None,())
                    serial_thread.start()
                except (KeyboardInterrupt, SystemExit):
                    print "start()"
                    self.quit()
                    raise
                except:
                    self.quit()

        def read_thread(self):
                '''
                The thread used to read incoming serial data.
                '''
                dat_new = ''
                dat_old = ''
                #Loops until the connection is broken, or is instructed to quit
                try:
                    while self.is_open():
                        #Instructed to quit
                        if self.exit:
                                break
                        if dat_new:
                                dat_old = dat_new
                                dat_new = ''
                        dat_old = dat_old + self.buffer()
                        #print dat_old
                        if re.search("\r\n", dat_old):
                                try:
                                        self.serial_data, dat_new = dat_old.split("\r\n")
                                        #print self.serial_data
                                except:
                                        pass
                                #The checksum is correct, so the data will be deconstructed
                                if self.checksum(self.serial_data):
                                        self.check_type()
                                dat_old = ''
                except (KeyboardInterrupt, SystemExit):
                    print "read_threads()"
                    self.quit()
                    raise

        def is_open(self):
                '''
                Checks whether the serial connection is still open.
                '''
                return self.serial_dev.isOpen()

        def buffer(self):
                '''
                Creates a buffer for serial data reading. Avoids reading lines for better performance.
                '''
                dat_cur = self.serial_dev.read(1)
                x = self.serial_dev.inWaiting()
                if x: dat_cur = dat_cur + self.serial_dev.read(x)
                return dat_cur

        def make_checksum(self,data):
                '''
                Calculates a checksum from a INS string.

                Keyword arguments:
                data -- the INS string to create

                '''
                crc = 0
                # Remove ! or $ and *xx in the sentence
                data = data[data.rfind('$')+1:data.rfind('*')]
                for s in data:
                        crc ^= ord(s)
                return "0x%X" % crc

        def checksum(self,data):
                '''
                Reads the checksum of an INS sentence.

                Keyword arguments:
                data -- the INS sentence to check

                '''
                try:				
                        supplied_csum = data[data.rfind('*')+1:data.rfind('*')+3]
                        # Create an integer of the two characters after the *, to the right
                        # supplied_csum = int(data[data.rfind('*')+1:data.rfind('*')+3], 16)
                except (KeyboardInterrupt, SystemExit):
                        print "checksum()"
                        self.quit()
                        raise
                except:
                        return ''
                # Create the checksum
                csum = self.make_checksum(data)
                # Compare and return
                supplied_csum = '0x' + supplied_csum
                if csum == supplied_csum:
                        return True
                else:
                        return False
                        print "csum failed"

        def check_type(self):
                '''
                Reads the sentence type, and directs the data to its respective function.
                '''
                self.serial_data = self.serial_data.split('*')
                #Splits up the INA data by comma
                self.serial_data = self.serial_data[0].split(',')
                #Incoming serial data is INS related
                if self.serial_data[0][3:6] == 'INS':
                        self.ins_ins()

        def ins_ins(self):
                '''
                Deconstructs INS sentence.
                '''
                
                a = time.time()
                #print "Time: \t{}".format(a-self.ttime)
                if (a-self.ttime) < 0.1:
                    return
                self.ttime = a
                
                try:
                    self.data_ins['time'] = str(self.serial_data[1])
                    self.data_ins['week'] = str(self.serial_data[2])
                    self.data_ins['head'] = str(self.serial_data[4])
                    self.data_ins['pitch'] = str(self.serial_data[5])
                    self.data_ins['roll'] = str(self.serial_data[6])
                    self.data_ins['lat'] = self.serial_data[7]
                    self.data_ins['long'] = self.serial_data[8]
                    self.data_ins['alt'] = str(self.serial_data[9])
                    self.data_ins['localtime'] = datetime.datetime.now().strftime("%s.%f")
                    #Stores data to the DB
                    self.dbstore()
                    
                    print self.data_ins['localtime']
                    print "\n#####################################################"
                    print "Localtime: \t\t",self.data_ins['localtime']
                    print "---------------------------------------"
                    print "time is %s and week is %s" % (self.data_ins['time'],self.data_ins['week'])
                    print "orientation is  YAW: %s PITCH: %s ROLL: %s" % (self.data_ins['head'],self.data_ins['pitch'],self.data_ins['roll'])
                    print "GPS is %s ; %s" % (self.data_ins['lat'],self.data_ins['long'])
                    print "altitude is %s" % self.data_ins['alt']
                    print "#####################################################\n"
                    
                except (KeyboardInterrupt, SystemExit):
                    print "ins_ins()"
                    raise
                except Exception as e:
                    print e
        
        def dbstore(self):
            if self.exit == False and self.clockFlag == True:
                try:
                    sql = "INSERT INTO `auvsi`.`INS` (`localtime`, `time`, `week`, `heading`, `pitch`, `roll`, `lat`, `lon`, `alt`) "
                    sql += "VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');".format(self.data_ins['localtime'], self.data_ins['time'], self.data_ins['week'], self.data_ins['head'], self.data_ins['pitch'], self.data_ins['roll'], self.data_ins['lat'], self.data_ins['long'], self.data_ins['alt'])
                    self.cur.execute(sql)
                    self.db.commit()
                    return True
                except (KeyboardInterrupt, SystemExit):
                    print "dbstore()"
                    raise
                except Exception as e:
                    print "### DB error!\n ###"
                    print "Error: \n{}\n".format(e)
                    print "SQL Query: {}\n".format(sql)
                    return False
            else:
                try:
                    self.clockFlag = setTime(self.data_ins['week'], self.data_ins['time'])
                except Exception, e:
                    print e
                return False
        

        def quit(self):
                '''
                Enables quiting the serial connection.
                '''
                self.exit = True
                self.cur.close()
                self.db.close()



if __name__ == '__main__':
    # serial_location = '/dev/ttyUSB0'
    USBDevices = glob.glob("/dev/ttyUSB*")
    if len(USBDevices) == 0:
        raise Exception("No ttyUSB devices found!")
    
    serial_location = USBDevices[0]
    serial_baudrate = 115200
    serial_timeout = 5

    #Provides the required serial device info
    nmea = INS(serial_location,serial_baudrate,serial_timeout)
    
    #Starts the serial connection
    nmea.start()
    try:
        while (nmea.exit == False):
            time.sleep(0.01)
    except:
        print "Shutting down INS service!"
        nmea.exit = True
        raise
