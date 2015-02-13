#!/usr/bin/python
'''
@author: Eli Hayoon
'''
from shapely.geometry import Point, Polygon
import logging
import traceback

def pointZoneDist(zone, point, delta):
    Re = 6371*1000 # Earth's radius in meters
    pi = 3.141592653589793
    deg2rad = pi/180.0
    
    p = Point(float(point[0]), float(point[1]))
    
    dist = zone.distance(p)*deg2rad*Re # Distance in meters
    return dist < delta


def initSearchZone(file = "/var/auvsi/searchZone.txt"):
    logger = logging.getLogger("DataHandler")
    with open(file, 'r') as gfile:
        tmp = gfile.readlines()
    
    cords = list()
    
    for point in tmp:
        try:
            p = point.replace("\n","").replace("\r","").split(",")
            cords.append(((float(p[0]),float(p[1]))))
        except:
            print "Error loading search zone polygon"
            print traceback.format_exc()
            logger.error("Error loading search zone polygon\n{}".format(e), exc_info=True)
    
    if len(cords) >= 3:
        zone = Polygon(cords)
        return zone
    
    return None
    
    
if __name__ == '__main__':
    print initSearchZone()