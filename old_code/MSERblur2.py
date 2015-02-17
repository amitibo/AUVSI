#!/usr/bin/python

import cv2
import datetime
import glob
import math
import MySQLdb
import auvsiDB
from time import time
from shapely.geometry import box
import numpy as np
import pyexiv2
import traceback

img_prefix = ""
ext = "jpg"
img_dir = "//var//www//images//"
crop_prefix = "crop_"
crop_ext = "jpg"
crop_dir = "//var//www//crops//"

host = "localhost"
user = "openCV"
passwd = "rK8sFzmWVFJ4CMm5"
dbname = "openCV"


def processImage(img, altitude, lon, lat, groll, gpitch, gyaw, resize_factor = 4, isActive = False, toBlur = 0, mser_params = {'_delta' : 4, '_min_area' : 70, '_max_area' : 87616, '_max_variation' : 0.1, '_min_diversity' : 0.2, '_max_evolution' : 200, '_area_threshold' : 1.0, '_min_margin' : 0.003, '_edge_blur_size' : 5}, downsample = 2):
    # Runs mser on input image, stores results to DB
    debug = False
    starttime = time()
    #Load image 
    try:
        # Change exif orientation flag to '1' (Horizontal)
        fixExif(img)
        frameOrig = cv2.imread(img, cv2.CV_LOAD_IMAGE_COLOR)
        
        mser_params['_delta'] = 10
        mser_params['_min_area'] = 578/(downsample**2)
        mser_params['_max_area'] = 87616/(downsample**2)
         
        mser_params['_max_variation'] =  0.1
        mser_params['_min_diversity'] =  0.4 
        mser_params['_area_threshold'] =  1.0
        mser_params['_min_margin'] =  0.003
        
        newshape = (frameOrig.shape[1]/downsample, frameOrig.shape[0]/downsample)
        frame = cv2.resize(frameOrig,newshape)

    except Exception as e:
        print "unable to open file: ",e
        print traceback.format_exc()
        return 0

    
    start = datetime.datetime.now()
    db = MySQLdb.connect(host = auvsiDB.host, user = auvsiDB.user, passwd = auvsiDB.passwd, db = auvsiDB.db)
    cur = db.cursor()
    
    # Get image ID from the DB
    sql = "INSERT INTO `{}`.`images` (`id`, `time`, `milisec`, `alt`, `lon`, `lat`, `groll`, `gpitch`, `gyaw`, `src`, `sent`)".format(auvsiDB.db)
    sql = sql + "VALUES (NULL, '{}',  MICROSECOND('{}'), '{}', '{}', '{}', '{}', '{}', '{}', '{}', 'false');".format(str(start), str(start), altitude, lon, lat, groll, gpitch, gyaw,str(img))
    #print sql
    cur.execute(sql)
    iidx = cur.lastrowid
    firstDB = time()
    
    # Creates a new frame to be resized and sent to the ground
    shape = (frameOrig.shape[1]/resize_factor, frameOrig.shape[0]/resize_factor)
    resizeImage(frameOrig, shape, img_dir, img_prefix, iidx, ext)
    
    # Runs MSER if isActive is set to true, otherwise resize and sends the picture
    areas = list()
    newRects = list()
    
    # Runs MSER
    if isActive == True:
        
        if toBlur == 0:
            frame2 = frame
        else:
            frame2 = cv2.medianBlur(frame, 7)
        mser_channel = genMserChannel(frame2, alpha = 0.2, beta = 20)
        if debug == True: cv2.imwrite("{}{}{}_mser.{}".format(img_dir, img_prefix, iidx, ext), mser_channel)
        
        mser = cv2.MSER(**mser_params)
        areas = mser.detect(mser_channel)
        newRects = mserToRects(areas, maxX = frame.shape[1], maxY = frame.shape[0])
        
    # Creates a copy of the image to draw areas created by MSER
    if debug == True:
        tmpframe = frame.copy()        
        hulls = [cv2.convexHull(p.reshape(-1, 1, 2)) for p in areas]
        cv2.polylines(tmpframe, hulls, 1, (0, 255, 0), thickness=1)

    cropnum = 0
    w = 181 # w = int(128*math.sqrt(2)) = 181
    # Insert targets to DB
    for targ in newRects:
        y_min = targ[1]*downsample
        y_max = (targ[1] + targ[3])*downsample
        x_min = targ[0]*downsample
        x_max = (targ[0] + targ[2])*downsample
        
        if debug == True: cv2.rectangle(tmpframe, (targ[0], targ[1]), (targ[0]+targ[2], targ[1]+targ[3]), (0, 0, 255), thickness=1)
        cropped  = frameOrig[(y_min):(y_max), (x_min):(x_max)]
        if np.std(cropped) > 4:
            resized = cv2.resize(cropped, (w,w))
            cv2.imwrite("{}{}{}_{}.{}".format(crop_dir, crop_prefix, iidx, cropnum, crop_ext), resized)
    
            sql = "INSERT INTO `{}`.`crops` (`fatherid`, `id`, `c1x`, `c1y`, `c2x`, `c2y`, `c3x`, `c3y`, `c4x`, `c4y`) VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}', '{}');".format(auvsiDB.db, iidx, cropnum, x_min, y_min, x_max, y_min, x_max, y_max, x_min, y_max)
            cur.execute(sql)
            cropnum+=1
    
    db.commit()
    cur.close()
    db.close()
            
    if debug == True: cv2.imwrite("{}{}{}_debug.{}".format(img_dir, img_prefix, iidx, ext), tmpframe)
    print "Ended: ",img, "\ttook: ", time()-starttime,"\ttargets: ",cropnum

	
def genMserChannel(img, alpha = 0.2, beta = 20):
    # Converts image to HSV, process MSER on a single channel
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    hsv=hsv.astype('float32')
    h = hsv[:,:,0]
    s = hsv[:,:,1]
    v = hsv[:,:,2]
    mser_channel = s/(1 + np.exp(-(v/255 - alpha)*beta))
    mser_channel = mser_channel.astype('uint8')  
    return mser_channel
    

def divIntersections(mat):
    newMat = mat.copy().astype('float')
    for i in range(len(newMat)): newMat[i] = newMat[i]/newMat[i,i]
    return newMat
    #print np.array_str(newMat, max_line_width=1000000)
    for row in range(0,len(mat)):
        tmprow = list()
        divider = float(mat[row][row])
        for col in range(0,len(mat)):
            tmprow.append(float(mat[row][col])/divider)
        newMat.append(tmprow)
    return newMat
    
    
def rectToPolygon(rect):
    return box(rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3])
    
    
def distanceIsLessThan(x,y,delta):
    # Gets two rectangles in the form of (x,y, width, height) and returns 1
    # if the distance between their centers is less than 'delta', otherwise 0.
    A_x = x[0]+float(x[2])/2
    A_y = x[1]+float(x[3])/2
    
    B_x = y[0]+float(y[2])/2
    B_y = y[1]+float(y[3])/2
    
    dist = math.pow(A_x - B_x,2) + math.pow(A_y - B_y,2)
    dist = math.sqrt(dist)
    if dist < delta: return 1
    return 0


def getNeighborsMatrix(rects, delta):
    n = len(rects)
    NMat = np.zeros([n, n], dtype='int_')
    
    for idx in range(0,n):
        for tdx in range(0,idx+1):
            NMat[idx,tdx] = distanceIsLessThan(rects[idx], rects[tdx], delta)
            NMat[tdx,idx] = NMat[idx,tdx]
    return NMat


def getIntersectionAreaMatrix(rects):
    n = len(rects)
    NMat = np.zeros([n, n], dtype='int_')
    
    for idx in range(0,n):
        for tdx in range(0,idx+1):
            A = rectToPolygon(rects[idx])
            B = rectToPolygon(rects[tdx])
            area = A.intersection(B).area
            NMat[idx,tdx] = area
            NMat[tdx,idx] = area
    return NMat


def getPMatrix(mat):
    d = np.diag(mat).astype('float')

    rep = cv2.repeat(d, 1, len(d))
    return mat/rep


def moveRectIntoImage(rect, maxX = 4000, maxY = 3000):
    (x,y,w,h) = rect
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    if x+w > maxX:
        w = maxX - x
    if y+h > maxY:
        h = maxY - y
    return (x,y,w,h)


def rectIsNearEdge(rect, delta):
    (x,y,w,h) = rect
    dist = min(x+w/2, y+h/2)
    if dist < delta:
        return True
    return False
    
def mserToRects(areas, maxX, maxY):
    # Combines close targets to rectangles
    targets = list()  
    minDistFromEdge = 0
    # Fits an ellipse around the detected area
    # Adds the bounding rectangle to the target list if height/width ratio is less than 2.2
    for p in areas:
        rotatedRect = cv2.fitEllipse(p)
        ratio = max(rotatedRect[1])/min(rotatedRect[1])
        loc = rotatedRect[0]
        cropSize = 1.3*1.3*math.sqrt(2)
        mxAx = max(rotatedRect[1])*cropSize
        ax = (mxAx,mxAx)
        r_ = (int(loc[0]-ax[0]/2),int(loc[1]-ax[1]/2),int(ax[0]),int(ax[1]))
        if ratio <= 2.2 and not rectIsNearEdge(r_, minDistFromEdge):
            targets.append(r_)
        
    n = len(targets)
    newRects = list()
    mat = getNeighborsMatrix(targets,100)
    
    # Goes over the matrix
    for rowid in range(0,n):
        # If the row is empty - continue
        if mat[rowid].max() == 0:
            continue
        
        nonEmpty = list() # Stores index of non-empty cells (I.e. close targets)
        for i in range(0,n):
            if mat[rowid,i] == 1:
                nonEmpty.append(i)
                mat[rowid,i] = 0
                # If found '1' in column X, sets the X'th row to 0.
                mat[i].fill(0)

        if len(nonEmpty) == 1:
            temp_rect = moveRectIntoImage(targets[nonEmpty[0]], maxX, maxY)
            newRects.append(temp_rect)
        elif len(nonEmpty) > 1:
            tmp = list()
            for val in nonEmpty:
                tmp.append(targets[val])
            intersectionMatrix = getIntersectionAreaMatrix(tmp)
            p = divIntersections(intersectionMatrix) # normalized intersections
            DBL_EPSILON = np.finfo(np.float32).eps
            P = p + p.T + DBL_EPSILON

            p0 = p / P # Element wise
            p1 = p.T / P # Element wise

            p0_ = p0 + DBL_EPSILON
            p0_ = np.log2(p0_) # Element wise

            p1_ = p1 + DBL_EPSILON
            p1_ = np.log2(p1_) # Element wise

            e = -(p0*p0_ + p1*p1_) # Element wise
            np.fill_diagonal(e, DBL_EPSILON)
            sumRow = np.sum(e, 0) # Sums all columns to a single row [[a, b],[c,d]] -> [a+c, b+d]

            maxIndex = np.argmax(sumRow) # Returns the index of the (first) maximum value in the sum 1D array
            temp_rect = moveRectIntoImage(targets[nonEmpty[maxIndex]])            
            newRects.append(temp_rect)

    return newRects

def resizeImage(frame, shape, img_dir, img_prefix, iidx, ext):
    vis = cv2.resize(frame, shape)
    cv2.imwrite("{}{}{}.{}".format(img_dir, img_prefix, iidx, ext), vis)

def fixExif(img):
    try:
        imgExif = pyexiv2.ImageMetadata(img)
        imgExif.read()
        imgExif['Exif.Image.Orientation'].value = 1
        imgExif.write()
        imgExif = None
        return True
    except:
        return False

if __name__ == '__main__':
#        path = 'C:/picsWithTargets/'
#        f = []
#        for (dirpath, dirnames, filenames) in walk(path):
#            f.extend(filenames)
#            break
#        
#        for imgname in filenames:
#            processImage(path+imgname , 1, 1, 1, 1, 1, 1, resize_factor = 4, isActive = True, hsv_channel = 3)
#		processImage('/var/auvsi/img7.jpg' , 1, 1, 1, 1, 1, 1, resize_factor = 4, isActive = True, hsv_channel = 3)
        pics = glob.glob("/var/www/pyp/auvsi/*")
        #print pics
        for pic in pics:
            processImage(pic , 1, 1, 1, 1, 1, 1, resize_factor = 2, isActive = True, toBlur = 0)
        
        
