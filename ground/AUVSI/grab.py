'''
Created on Nov 25, 2013
@author: elius

Edited by: Ori Ashur
03.01.2015

'''


import urllib
import urllib2
import os
import sqlite3
import time
from xml.dom import minidom
import socket


local_image_dir = r".\data\images\\"
local_crops_dir = r".\data\crops\\"
local_xml_dir   = r".\data\xml\\"
local_db_dir    = r".\data\\"


addr            = "http://192.168.1.12:8070/"  # ODROID web address
loop_delay      = 0.1 # Time to wait after a failed request

con = sqlite3.connect(local_db_dir + "auvsi.db")
cur = con.cursor()
#"CREATE TABLE xmls (id INTEGER PRIMARY KEY, status TEXT, src TEXT)"

def grab(action = ""):
    '''
    Grabs an xml file from the ODROID over HTTP.
    Parse & modify the relevant parts.
    Saves images, crops and the xml file to disk. 
    '''
    
  
    try:
        url = addr + "db.php"
        if len(action) > 0:
            url = url + "?action=" + action
        xmlfile = urllib2.urlopen(url)
        
        #get data for full compressed images
        xmldoc = minidom.parse(xmlfile)
        image_id = xmldoc.getElementsByTagName('image')[0].attributes['id'].value 
        image_src = xmldoc.getElementsByTagName('large_img')[0].attributes['src'].value
        #gets the images from db.php (on odroid)
        urllib.urlretrieve(addr + image_src, local_image_dir + os.path.basename(image_src))
        #saving the local path for the downloaded image
        xmldoc.getElementsByTagName('large_img')[0].attributes['src'].value = local_image_dir + os.path.basename(image_src)
        
        #get data for cropped images
        crop_list = xmldoc.getElementsByTagName('img')
        #getting all the "suspects" for targets as the MSER recognised from the "large" image above
        for crop in crop_list:
            urllib.urlretrieve(addr + crop.attributes['src'].value, local_crops_dir + os.path.basename(crop.attributes['src'].value))
            crop.attributes['src'].value = local_crops_dir + os.path.basename(crop.attributes['src'].value)
        
        #saves xml file on local machine
        f = open(local_xml_dir + image_id + ".xml", 'w') 
        xmldoc.writexml(f)
        f.close()
        
        #update sql DB on local machine
        sql = "INSERT INTO xmls (id, status, src) VALUES({},'false', '{}')".format(image_id, local_xml_dir + image_id + ".xml")
        cur.execute(sql)
        print time.strftime("%Y-%m-%d %H:%M:%S"),"Received image ID:",image_id
        con.commit()
    
    except IndexError:
        time.sleep(loop_delay)
    except (urllib2.URLError, urllib2.HTTPError):
        print time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),"urllib2 error - connection working?"
        time.sleep(loop_delay)
    except socket.error:
        print time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),"Socket error - connection working?"
        time.sleep(loop_delay)
    except Exception as e:
        print time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()),e
        time.sleep(loop_delay) # Wait for 100ms
        
    
if __name__ == '__main__':
    try:
        while True:
            grab()
    except (KeyboardInterrupt, SystemExit):
            print "got keyboard int"
            cur.close()
            db.close()
            time.sleep(5)
    except Exception as e:
        print e
        time.sleep(5)
        raise