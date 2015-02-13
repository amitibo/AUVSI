#!/usr/bin/python
'''
@author: Eli Hayoon
'''
import subprocess
import datetime
import os
import glob
import MySQLdb
import time
import MSERblur2
import multiprocessing
import auvsiDB
import threading
import urllib
import json
import re
import logging
from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
import gistools

toLoop = True
PORT_NUMBER = 8080
mser_active = True
queue_size = 0
toBlur = 0
mser_params_ziv = {'_delta' : 5, '_min_area' : 60,  '_max_area' : 14400, '_max_variation' : 0.25,   '_min_diversity' : 0.2, '_max_evolution' : 200, '_area_threshold' : 1.01,   '_min_margin' : 0.003,  '_edge_blur_size' : 5}
mser_params_aar = {'_delta' : 10, '_min_area' : 144, '_max_area' : 21904, '_max_variation' : 0.1,    '_min_diversity' : 0.4, '_max_evolution' : 200, '_area_threshold' : 1.0,    '_min_margin' : 0.003,  '_edge_blur_size' : 5}
mser_params = mser_params_aar
last_image = time.time()
QU = multiprocessing.Queue()


logger = logging.getLogger("DataHandler")
logger.setLevel(logging.INFO)

# create a file handler for logs
logFiles = set(glob.glob('/var/auvsi/logs/*.log*'))
print logFiles
if len(logFiles) == 0:
    logFile = "/var/auvsi/logs/dataHandler.log"
else:
    logFile = "/var/auvsi/logs/dataHandler.log.{}".format(len(logFiles))
handler = logging.FileHandler(logFile)
handler.setLevel(logging.INFO)

# create a logging format
formatter = logging.Formatter('%(asctime)s - %(funcName)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# add the handlers to the logger
logger.addHandler(handler)
logger.info("Started data handler...")


def s110shoot(tv = 5000, sv = 50, av = 4):
    logger = logging.getLogger("DataHandler")
    try:
        # Create new dir to hold images.
        imageDir = "/var/www/pyp/"
        dirname = datetime.datetime.now().strftime("%Y-%m-%d-%H:%M:%S")
        dirpath = imageDir + dirname
        os.mkdir(dirpath)
        os.chdir(dirpath)
        
        chdkptp = "/var/auvsi/chdkptp/chdkptp-sample.sh"
        params = ["-c", "-e\"remoteshoot -tv=1/{} -sv={} -av={} -cont=9000\"".format(tv,sv,av), "-e\"luar set_lcd_display(0);\""]
        delay = 2
        cmd = chdkptp + " " + params[0] + " " + params[1]
        logger.info("shoot command: "+cmd)
        proc = subprocess.Popen([cmd],shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(delay)
        if proc.poll() is not None:
            logger.error("###################### Shoot command error ######################")
            for x in proc.communicate(): print x
            return False
        else:
            logger.info("Shooting to:\t\t{}".format(dirpath))
            return dirpath
        
    except Exception as e:
            logger.error("Unable to run camera shoot command!\n{}".format(e), exc_info=True)
            return False

def s110init(zoom = 0):
    logger = logging.getLogger("DataHandler")
    logger.info("s110 init")
    chdkptp = "/var/auvsi/chdkptp/chdkptp-sample.sh"
    params = ["-c", "-erec", "-e\"luar enter_alt(); call_event_proc('SS.Create'); call_event_proc('SS.MFOn'); set_prop(222,0); set_focus(65000); set_prop(272,0); set_prop(105,3); set_zoom_speed(1); set_zoom({});\"".format(zoom)]
    try:
        cmd = chdkptp + " " + params[0] + " " + params[1] + " " + params[2]
        logger.info(cmd)
        output = subprocess.check_output([cmd], shell=True)
        print output
        logger.info("init: {}".format(output))
        if output.find("ERROR") >= 0 and output.find('already in rec') == -1:
            logger.error("Camera error:\n{}".format(output))
            return False
        return True
        
    except Exception as e:
        logger.error("Unable to run camera init command!\n{}".format(e), exc_info=True)
        return False


def s110kill():
    logger = logging.getLogger("DataHandler")
    chdkptp = "/var/auvsi/chdkptp/chdkptp-sample.sh"
    params = ["-c", "-e\"killscript;\""] 
    tries = 7
    delay = 5
    cmd = chdkptp + " " + params[0] + " " + params[1]
    logger.info("Stopping!\n{}".format(cmd))
    for i in range(tries):
        output = subprocess.check_output([cmd],shell=True)
        time.sleep(delay)


def loopImages(dirpath):
    logger = logging.getLogger("DataHandler")
    # Setup database connection, queue, image lists, multiprocessing parameters
    global toLoop
    global queue_size
    global toBlur
    global last_image
    global QU
    last_image = time.time()
    
    logger.info("Starting: \t\tloopImages({})".format(dirpath))
    db = MySQLdb.connect(host = auvsiDB.host, user = auvsiDB.user, passwd = auvsiDB.passwd, db = auvsiDB.db)
    cur = db.cursor()
    images = set()
    newImages = set()
    
    global mser_params
    global mser_active
    loop_delay = 0.1
    
    jobs = []
    MAX_JOBS = 3
    skew = 2.05
    
    searchZone = gistools.initSearchZone()
    searchZoneDelta = 5 # meters 
    
    processed = list()
    while toLoop:
        try:
            # Check for new images
            images = newImages
            time.sleep(loop_delay)
            newImages = set(glob.glob(dirpath+'/*.jpg'))
            # Add new images to queue
            for img in sorted(newImages - images):
                if img in processed:
                    print "duplicate ",img
                else:
                    # Sleep incase still writing image to disk
                    time.sleep(loop_delay*2)
                    imgtime = os.path.getmtime(img) - skew
                    sql = "SELECT *  FROM `INS` WHERE `localtime` >= {} ORDER BY `localtime` ASC LIMIT 1".format(imgtime)

                    ## DEBUG
                    db.commit() # Refresh data from database, otherwise old INS info would be obtained
                    cur.execute(sql)
                    ver = cur.fetchone()
                    
                    # If no matching INS entry set all to zero
                    if ver is None:
                        logger.error("Image date not found for image: {}, imgtime: {}".format(img, imgtime))
                        ver = list()
                        ver.append(0) # localtime
                        ver.append(0) # time
                        ver.append(0) # week
                        ver.append(0) # heading
                        ver.append(0) # pitch
                        ver.append(0) # roll
                        ver.append(0) # lat
                        ver.append(0) # lon
                        ver.append(0) # alt
                    # Add image to queue
                    mserInput = dict()
                    dist = gistools.pointZoneDist(searchZone,[ver[6],ver[7]],searchZoneDelta)
                    if dist == False:
                        ster = "Image {} out of range {},{}".format(img, ver[6], ver[7])
                        logger.info(ster)
                    mserInput = {'isActive':dist,"toBlur": toBlur, "img":img, "altitude":ver[8], "lon":ver[7], "lat":ver[6], "groll":ver[5], "gpitch":ver[4], "gyaw":ver[3], 'mser_params':mser_params}
                    processed.append(img)
                    logger.info("Inserted: {}".format(img))
                    QU.put(mserInput)
                    last_image = time.time()
                    ## DEBUG
                    #===============================================================
                    with open(img+'.txt', 'w') as the_file:
                        for verkey in sorted(mserInput):
                            if verkey not in ['toBlur', 'mser_params']:
                                the_file.write('{}:{}\n'.format(verkey, mserInput[verkey]))
                    #===============================================================
                    
            # if less than MAX_JOBS mser  processes are running, get an image from the queue and run mser.    
            n = len([1 for job in jobs if job.is_alive()])
            if n < MAX_JOBS and QU.empty() == False:
                tmp_mser_params = QU.get()
                if tmp_mser_params['isActive'] == True: tmp_mser_params['isActive'] = mser_active
                tmp_mser_params['mser_params'] = mser_params
                p = multiprocessing.Process(target=MSERblur2.processImage, kwargs = tmp_mser_params)
                logger.info("Pulled: {}".format(tmp_mser_params['img']))
                jobs.append(p)
                p.start()

            queue_size = QU.qsize()
            
            if queue_size == 0 and time.time() - last_image > 60:
                logger.info("One minute with no images - closing loopImages")
                print "One minute with no images - closing loopImages"
                break
            
            time.sleep(loop_delay)
        
        except KeyError:
            logger.error("keyError", exc_info=True)
        except (KeyboardInterrupt, SystemExit):
            logger.error("got keyboard int", exc_info=True)
            cur.close()
            db.close()
            break

        except Exception as inst:
            logger.error("Exception occured", exc_info=True)
            print "error:", inst
            
    cur.close()
    db.close()
#===============================================================================


def startShooting(zoom = 0, av = 4, tv = 5000, sv = 50):
    
    imageDir = "/var/www/pyp/"
    
    if s110init(zoom) == False:
        return False, "s110.initCam"
    dirpath = s110shoot(tv, sv, av)
    if dirpath == False:
        return False, "s110.shoot"
    return True, dirpath

def stopShooting():
    logger = logging.getLogger("DataHandler")
    thread = threading.Thread(target=s110kill)
    thread.start()
    logger.info("Killing time")
    return True
     
#===============================================================================

def genMsg(input):
    return "okay:{}".format(input)

def genError(input):
    return "error:{}".format(input)


class myHandler(BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        logger = logging.getLogger("DataHandler")
        msg = "%s - - [%s] %s\n" %(self.client_address[0], self.log_date_time_string(), format%args)
        logger.info(msg)


    #Handler for the GET requests
    def do_GET(self):
        logger = logging.getLogger("DataHandler")
        self.send_response(200)
        self.send_header('Content-type','text/html')
        self.end_headers()
        self.currentDir = False
        
        global mser_active
        global mser_params
        global queue_size
        global toBlur
        global toLoop
        global QU
        
        mser_allowed_params = ['_delta', '_min_area', '_max_area', '_max_variation', '_min_diversity', '_max_evolution', '_area_threshold', '_min_margin', '_edge_blur_size']
        output = ""
        try:
            if re.match(r'/startshoot', self.path):
                tmp = self.path[len('/startshoot')+1:]
                shoot_params = {'zoom':45,'tv':5000,'av':4,'sv':50}
                shoot_allowed_params = ['zoom', 'tv', 'av', 'sv']
                output = genError("startshoot")
				
                if len(tmp) > 0:
                    tmp = tmp.split('&')
                    for x in tmp:
                        x = x.split('=')
                        try:
                            shootval = int(x[1])
                        except:
                            try:
                                shootval = float(x[1])
                            except:
                                shootval = None
                     
                        if shootval is not None and x[0] in shoot_allowed_params:
                            shoot_params[x[0]] = shootval
                
                self.currentDir, reply = startShooting(**shoot_params)
                if self.currentDir == False:
                    output = genError(reply)
                else:
                    self.currentDir = reply
                    output = genMsg("shooting:"+reply)
                    toLoop = True
                    
                    thread = threading.Thread(target=loopImages, args=(reply,))
                    thread.start()
                    logger.info("Started MSER and shooting! {}".format(self.currentDir))   
                            
            elif self.path == "/stopshoot":
                if stopShooting():
                    output = genMsg("stopSooting in progress")
                else:
                    output = genError("stopSooting")

                
            elif self.path == "/stopmser":
                mser_active = False
                output = genMsg("stopmser")
            
            
            elif self.path == "/startmser":
                mser_active = True
                output = genMsg("startmser")
            

            ### Set mser channels
            elif self.path == "/bluroff":
                toBlur = 0
                output = genMsg("bluroff")
            
            elif self.path == "/bluron":
                toBlur = 1
                output = genMsg("bluron")
            
            elif self.path == "/mserval":
                toBlur = 2
                output = genMsg("mserval")
                        
            elif self.path == "/mser2h1v":
                toBlur = 3
                output = genMsg("mser2h1v")
            
            elif self.path == "/getgps":
                output = getLatestGps()
            
            elif self.path == "/clrqueue":
                while QU.empty() == False:
                    QU.get()
                output = genMsg("clearedQueue")
                    
            
            elif re.match(r'/setmser', self.path):
                tmp = self.path[len('/setmser')+1:]
                output = genError("setmser")
                if len(tmp) > 0:
                    tmp = tmp.split('&')
                    for x in tmp:
                        x = x.split('=')
                        try:
                            mserval = int(x[1])
                        except:
                            try:
                                mserval = float(x[1])
                            except:
                                mserval = None
                    
                        if mserval is not None and x[0] in mser_allowed_params:
                            mser_params[x[0]] = mserval
                            output = genMsg("setmser")
            
            elif self.path == "/links":
                f = open("/var/www/links.html")
                output = f.read()
                f.close()

            else:
                output = genStatus()

        except Exception as e:
            logger.error("Error: \n{}".format(e.message), exc_info=True)
        
        self.wfile.write(output)
        
        return

def getLatestGps():
    gpsDB = MySQLdb.connect(host = auvsiDB.host, user = auvsiDB.user, passwd = auvsiDB.passwd, db = auvsiDB.db)
    gpsCur = gpsDB.cursor()
    timeDiff = 10
    sql = "SELECT * FROM `INS` ORDER BY `localtime` DESC LIMIT 1"
    gpsDB.commit()
    gpsCur.execute(sql)
    ver = gpsCur.fetchone()
    gpsCur.close()
    gpsDB.close()
    
    if ver is None:
        output = "0,0,0"
        
    elif (float(datetime.datetime.now().strftime("%s.%f")) - float(ver[0])) < timeDiff:
        output = "{},{},{}".format(ver[8], ver[6],ver[7]) # alt, Lat, lon
    else:
        output = "0,0,0"

    return output


def genStatus():
    global mser_active
    global mser_params
    global queue_size
    global toBlur
    global last_image
    
    tempdict = dict(mser_params)
    tempdict['mser_active'] = str(mser_active)
    tempdict['blur'] = bluron(toBlur)
    tempdict['queue'] = queue_size
    tempdict['last_image'] = '%.2f' % (time.time() - last_image)

    templist = sorted(tempdict.items())
    templist.append(('cpu_temp',cpuTemp()))
    html = "<table class=\"myTable\">"

    for key,val in templist:        
        html += "<tr><td style='width:150px'>{}</td><td style='width:150px'>{}</td></tr>".format(key,val)
    html += "</table>"
    return html
   
'''
def genStatus2():
    global mser_active
    global mser_params
    global queue_size
    global toBlur
    global last_image
    
    tempdict = dict(mser_params)
    tempdict['mser_active'] = str(mser_active)
    tempdict['blur'] = bluron(toBlur)
    tempdict['queue'] = queue_size
    tempdict['last_image'] = time.time() - last_image
    return json.dumps(tempdict, indent=4, separators=(',', ': '))
'''

def bluron(num):
    if num == 0: return "no"
    return "yes"
    
def num2hsv(num):
    if num == 0: return "hue"
    if num == 1: return "saturation"
    if num == 2: return "value"
    if num == 3: return "2h1v"
    return None
    

def cpuTemp():
    try:
        with open('/sys/devices/virtual/thermal/thermal_zone0/temp', 'r') as f:
            temp = f.readlines()
            temp = float(temp[0].replace("\n",''))/1000.0
            if temp > 90.0:
                return "<font style='font-weight:bold;color:red;font-size:20px;'>{}</font>".format(temp)
            if temp > 80.0:
                return "<font style='font-weight:bold;color:orange;'>{}</font>".format(temp)
            if temp > 70.0:
                return "<font style='color:orange'>{}</font>".format(temp)
            return str(temp)
    except Exception as e:
        print e
        return "Unknown"
    
try:
    #loopImages('/var/www/pyp/2014-05-25-16:27:28/')
    server = HTTPServer(('', PORT_NUMBER), myHandler)
    logger.info('Started httpserver on port {}'.format(PORT_NUMBER))
    server.serve_forever()

except KeyboardInterrupt:
    print '^C received, shutting down the web server'
    toLoop = False
    server.socket.close()
