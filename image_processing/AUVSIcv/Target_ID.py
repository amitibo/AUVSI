from __future__ import division
import numpy as np
from scipy import stats
from scipy import misc
import cv2
import math
from numpy import unravel_index
import  matplotlib.pyplot as plt
from pytesseract import image_to_string
from PIL import Image as Im
from scipy import ndimage
from scipy import signal
import matplotlib.pyplot as plt
import struct
import scipy
import scipy.misc
import scipy.cluster
import webcolors
#from AUVSIcv import qrtools

def RGB2HSV(RGB_Value):
    Temp = np.zeros([1,1,3],np.uint8)
    Temp[0][0][0] = RGB_Value[0]
    Temp[0][0][1] = RGB_Value[1]
    Temp[0][0][2] = RGB_Value[2]
    HSV = cv2.cvtColor(Temp,cv2.COLOR_RGB2HSV)
    return HSV[0][0][0],HSV[0][0][1],HSV[0][0][2]
    
    
def closest_colour(requested_colour):
    min_colours = {}
    for key, name in webcolors.css3_hex_to_names.items():
        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
        rd = (r_c - requested_colour[0]) ** 2
        gd = (g_c - requested_colour[1]) ** 2
        bd = (b_c - requested_colour[2]) ** 2
        min_colours[(rd + gd + bd)] = name
    return min_colours[min(min_colours.keys())]

def get_colour_name(requested_colour):
    try:
        closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
    except ValueError:
        closest_name = closest_colour(requested_colour)
        actual_name = None
    return actual_name, closest_name
def Contour_Extractor(Image):
    #Filtered_Image = np.uint8(signal.wiener(np.float32(Image),7))
    Filtered_Image = Image
    cv2.namedWindow('Original',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Original',Image)
    cv2.namedWindow('Filtered',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Filtered',Filtered_Image)
    cv2.waitKey(0)    

    #Outer contours
    
    HSV_Image = cv2.cvtColor(Filtered_Image,cv2.COLOR_RGB2HSV)
    Image_Value = HSV_Image[:,:,2]
    #Image_Value = HSV_Image[:,:,1]
    #Image_Value = np.uint8(np.float32(Image_Value)*255/np.float32(np.max(Image_Value)))
    Unused,Image_Value_2 = cv2.threshold(Image_Value, 127, 255,0)
    #Check threshold!!!!!

    Contour_Image = np.uint8(np.zeros(Image.shape))
    Contours,Unused_2 = cv2.findContours(Image_Value_2.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    #Contour Filtration
    if (len(Contours) > 1):
        Length_Vector = np.zeros(len(Contours))
        for i in range(len(Contours)):
            Length_Vector[i] = len(Contours[i])
        Max_Length = np.max(Length_Vector)
        Avg_Length = np.mean(Length_Vector)
        Tolerance = 20
        if (abs(Max_Length - Avg_Length) < Tolerance):
            return Contours,-1
        Contours = Contours[np.argmax(Length_Vector)]
    else:
        Contours = Contours[0]
    Color = [128,128,128]
    cv2.drawContours(Contour_Image,[Contours], -1, Color,-1)
    cv2.namedWindow('Target Contours',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Target Contours',Contour_Image)
    cv2.waitKey(0)  
    return Contours,0
def Contour_Extractor_2(Image):
    
    Tolerance = 40
    Image_2 = Image.copy()
    cv2.namedWindow('Original',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Original',Image)
    cv2.waitKey(0)    

    NUM_CLUSTERS = 2
    shape = Image_2.shape
    Image_2 = Image_2.reshape(scipy.product(shape[:2]), shape[2])

    codes, dist = scipy.cluster.vq.kmeans(Image_2, NUM_CLUSTERS)

    vecs, dist = scipy.cluster.vq.vq(Image_2, codes)         # assign codes
    counts, bins = scipy.histogram(vecs, len(codes))    # count occurrences
    index_max = scipy.argmax(counts)                    # find target color
    index_min = scipy.argmin(counts)                    # find bg color
    Target_Color = codes[index_max]

    #Add proper color check here!

    Target_R = Target_Color[0]
    Target_G = Target_Color[1]
    Target_B = Target_Color[2]
    Image_Value = Image.copy()
    Image_Value[Image_Value[:,:,0] > Target_R + Tolerance] = 0
    Image_Value[Image_Value[:,:,0] < Target_R - Tolerance] = 0
    Image_Value[Image_Value[:,:,1] > Target_G + Tolerance] = 0
    Image_Value[Image_Value[:,:,1] < Target_G - Tolerance] = 0
    Image_Value[Image_Value[:,:,2] > Target_B + Tolerance] = 0
    Image_Value[Image_Value[:,:,2] < Target_B - Tolerance] = 0
    Image_Value[Image_Value[:,:,:] != 0] = 255
    Image_Value = Image_Value[:,:,0]
    
    #Border check:
    Pix_Num = 10
    Im_Size = Image_Value.shape
    Border_Sum = sum(Image_Value[0,:]) + sum(Image_Value[Im_Size[0]-1,:]) + sum(Image_Value[:,0]) + sum(Image_Value[:,Im_Size[1]-1])
    if (Border_Sum > 255*Pix_Num):
        Image_Value = np.invert(Image_Value)
    
    #Outer contours
    Unused,Image_Value_2 = cv2.threshold(Image_Value, 127, 255,0)
    Contour_Image = np.uint8(np.zeros(Image.shape))
    Contours,Unused_2 = cv2.findContours(Image_Value_2.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    #Contour Filtration
    if (len(Contours) > 1):
        Length_Vector = np.zeros(len(Contours))
        for i in range(len(Contours)):
            Length_Vector[i] = len(Contours[i])
        Max_Length = np.max(Length_Vector)
        Avg_Length = np.mean(Length_Vector)
        Tolerance = 20
        if (abs(Max_Length - Avg_Length) < Tolerance):
            return Contours,-1
        Contours = Contours[np.argmax(Length_Vector)]
    else:
        Contours = Contours[0]
    Color = [128,128,128]
    cv2.drawContours(Contour_Image,[Contours], -1, Color,-1)
    cv2.namedWindow('Target Contours',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Target Contours',Contour_Image)
    cv2.waitKey(0)  
    return Contours,0

def Letter_Contour_Extractor(Image):
    cv2.namedWindow('Original',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Original',Image)
    cv2.waitKey(0)       
    Contour_Image = np.uint8(np.zeros(Image.shape))
    Image_1D = Image[:,:,0]
    Contours,Unused_2 = cv2.findContours(Image_1D.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)

    #Contour Filtration
    if (len(Contours) > 1):
        Length_Vector = np.zeros(len(Contours))
        for i in range(len(Contours)):
            Length_Vector[i] = len(Contours[i])
        Max_Length = np.max(Length_Vector)
        Avg_Length = np.mean(Length_Vector)
        Tolerance = 20
        if (abs(Max_Length - Avg_Length) < Tolerance):
            return Contours,-1
        Contours = Contours[np.argmax(Length_Vector)]
    else:
        Contours = Contours[0]
    Color = [128,128,128]
    cv2.drawContours(Contour_Image,[Contours], -1, Color,-1)
    cv2.namedWindow('Letter Contours',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Letter Contours',Contour_Image)
    cv2.waitKey(0)  
    return Contours,0    
    
def Target_Shape_Extractor(Image,Contours,Shape_Name_DB_Path,Shape_DB_Path):  
    Cont_X = np.zeros([len(Contours)],np.uint8)
    Cont_Y = np.zeros([len(Contours)],np.uint8)
    for i in range(len(Contours)):
        Cont_X[i] = Contours[i][0][0]
        Cont_Y[i] = Contours[i][0][1]    
        
    #Cont_X = np.zeros([len(Contours[0])],np.uint8)
    #Cont_Y = np.zeros([len(Contours[0])],np.uint8)
    #for i in range(len(Contours[0])):
        #Cont_X[i] = Contours[0][i][0][0]
        #Cont_Y[i] = Contours[0][i][0][1]       

        #Change paths later!
    #Shape_Name_DB_Path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Shapes\Contour_Name_DB.npy'
    #Shape_DB_Path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Shapes\Contour_DB.npy'
    Shape_Name_DB = np.load(Shape_Name_DB_Path)
    Shape_DB = np.load(Shape_DB_Path)
    Shape_Num,Contour_Vector_Length = Shape_DB.shape
        
    Ratio = Contour_Vector_Length/len(Cont_X)  
    Short_X = ndimage.interpolation.zoom(np.float32(Cont_X),Ratio)
    Short_Y = ndimage.interpolation.zoom(np.float32(Cont_Y),Ratio)
    Vector_Size = len(Short_X)
    Short_X = np.float32(Short_X)
    Short_Y = np.float32(Short_Y)
    
    Gamma_Vector = np.zeros([Vector_Size],np.complex128)
    for i in range(Vector_Size):
        if (i == Vector_Size - 1):
            Gamma_Vector[i] = (Short_X[0]-Short_X[i]) + (Short_Y[0]-Short_Y[i])*1j
        else:
            Gamma_Vector[i] = (Short_X[i+1]-Short_X[i]) + (Short_Y[i+1]-Short_Y[i])*1j
    Norm = np.sqrt(sum(pow(np.absolute(Gamma_Vector),2)))
    #Norm = np.sqrt(abs(np.dot(Gamma_Vector,Gamma_Vector)))
    Gamma_Vector = Gamma_Vector / Norm
    
    Corr_Vector = np.zeros([Shape_Num],np.complex128)
    for i in range(Shape_Num):
        Local_Corr_Vector = np.zeros([Contour_Vector_Length],np.complex128)
        for j in range(Contour_Vector_Length):
            Local_Corr_Vector[j] = np.absolute(np.dot(Shape_DB[i],np.conj(np.roll(Gamma_Vector,j))))
        Corr_Vector[i] = np.max(Local_Corr_Vector)    
        
    Shape_Name = Shape_Name_DB[np.argmax(Corr_Vector)]
    Shape_Corr = np.max(Corr_Vector)
    return Shape_Name,Shape_Corr

def Color_Extractor(Image,Contours):
    Contour_Image = np.uint8(np.zeros(Image.shape))
    Color = [1,1,1]
    cv2.drawContours(Contour_Image, [Contours], -1, Color,-1)    
    Cropped_Target = np.multiply(Contour_Image,Image)
    cv2.namedWindow('Cropped target for color',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Cropped target for color',Cropped_Target)
    cv2.waitKey(0)      
    
    NUM_CLUSTERS = 3
    shape = Cropped_Target.shape
    Cropped_Target = Cropped_Target.reshape(scipy.product(shape[:2]), shape[2])
    
    codes, dist = scipy.cluster.vq.kmeans(Cropped_Target, NUM_CLUSTERS)
    
    vecs, dist = scipy.cluster.vq.vq(Cropped_Target, codes)         # assign codes
    counts, bins = scipy.histogram(vecs, len(codes))    # count occurrences
    index_max = scipy.argmax(counts)                    # find target color
    index_min = scipy.argmin(counts)                    # find letter color
    peak_1 = codes[index_max] 
    Black_Thresh = 20
    if (peak_1[0] < Black_Thresh and peak_1[1] < Black_Thresh and peak_1[2] < Black_Thresh):
        Temp = np.array([0,1,2])
        Temp[Temp == index_max] = -1
        Temp[Temp == index_min] = -1
        peak_1 = codes[np.max(Temp)]  
    peak_2 = codes[index_min]
    if (peak_2[0] < Black_Thresh and peak_2[1] < Black_Thresh and peak_2[2] < Black_Thresh):
        Temp = np.array([0,1,2])
        Temp[Temp == index_max] = -1
        Temp[Temp == index_min] = -1
        index_mid = np.max(Temp)
        peak_2 = codes[index_mid]
    
    actual_name, Target_Color_Name = get_colour_name((peak_1[0],peak_1[1],peak_1[2]))  
    actual_name, Letter_Color_Name = get_colour_name((peak_2[0],peak_2[1],peak_2[2])) 
    return peak_1,peak_2,Target_Color_Name,Letter_Color_Name
    
def Letter_Extractor(Image,Contours,Letter_Name_DB_Path,Letter_DB_Path,Letter_Color):
    Tolerance = 30
    Contour_Image = np.uint8(np.zeros(Image.shape))
    Color = [1,1,1]
    cv2.drawContours(Contour_Image, [Contours], -1, Color,-1)    
    Cropped_Target = np.multiply(Contour_Image,Image)
    cv2.namedWindow('Cropped target for letter',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Cropped target for letter',Cropped_Target)
    cv2.waitKey(0)        

    Letter_R = Letter_Color[0]
    Letter_G = Letter_Color[1]
    Letter_B = Letter_Color[2]
    Image_Value = Cropped_Target
    Image_Value[Image_Value[:,:,0] > Letter_R + Tolerance] = 0
    Image_Value[Image_Value[:,:,0] < Letter_R - Tolerance] = 0
    Image_Value[Image_Value[:,:,1] > Letter_G + Tolerance] = 0
    Image_Value[Image_Value[:,:,1] < Letter_G - Tolerance] = 0
    Image_Value[Image_Value[:,:,2] > Letter_B + Tolerance] = 0
    Image_Value[Image_Value[:,:,2] < Letter_B - Tolerance] = 0
    Image_Value[Image_Value[:,:,:] != 0] = 255
    
    
    Contours_Letter,Contour_Error = Letter_Contour_Extractor(Image_Value)
    
    
    Color = [128,128,128]
    cv2.drawContours(Contour_Image, [Contours_Letter], -1, Color,-1)
    cv2.namedWindow('Letter Contours',flags=cv2.WINDOW_NORMAL)
    cv2.imshow('Letter Contours',Contour_Image)
    cv2.waitKey(0)    
    
    Cont_X = np.zeros([len(Contours_Letter)],np.uint8)
    Cont_Y = np.zeros([len(Contours_Letter)],np.uint8)
    for i in range(len(Contours_Letter)):
        Cont_X[i] = Contours_Letter[i][0][0]
        Cont_Y[i] = Contours_Letter[i][0][1]    
    
        #Change paths later!
    #Shape_Name_DB_Path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Shapes\Contour_Name_DB.npy'
    #Shape_DB_Path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Shapes\Contour_DB.npy'
    Shape_Name_DB = np.load(Letter_Name_DB_Path)
    Shape_DB = np.load(Letter_DB_Path)
    Shape_Num,Contour_Vector_Length = Shape_DB.shape
    
    Ratio = Contour_Vector_Length/len(Cont_X)  
    Short_X = ndimage.interpolation.zoom(np.float32(Cont_X),Ratio)
    Short_Y = ndimage.interpolation.zoom(np.float32(Cont_Y),Ratio)
    Vector_Size = len(Short_X)
    Short_X = np.float32(Short_X)
    Short_Y = np.float32(Short_Y)
    
    Gamma_Vector = np.zeros([Vector_Size],np.complex128)
    for i in range(Vector_Size):
        if (i == Vector_Size - 1):
            Gamma_Vector[i] = (Short_X[0]-Short_X[i]) + (Short_Y[0]-Short_Y[i])*1j
        else:
            Gamma_Vector[i] = (Short_X[i+1]-Short_X[i]) + (Short_Y[i+1]-Short_Y[i])*1j
    Norm = np.sqrt(sum(pow(np.absolute(Gamma_Vector),2)))
    Gamma_Vector = Gamma_Vector / Norm
    
    Corr_Vector = np.zeros([Shape_Num],np.complex128)
    Angle_Vector = np.zeros([Shape_Num],np.complex128)
    for i in range(Shape_Num):
        Local_Corr_Vector = np.zeros([Contour_Vector_Length],np.complex128)
        for j in range(Contour_Vector_Length):
            Local_Corr_Vector[j] = (np.dot(Shape_DB[i],np.conj(np.roll(Gamma_Vector,j))))
        Corr_Vector[i] = np.max(np.absolute(Local_Corr_Vector))
        Temp = np.argmax(np.absolute(Local_Corr_Vector))
        Angle_Vector[i] = np.angle(Local_Corr_Vector[Temp],deg=True)
        
    Shape_Name = Shape_Name_DB[np.argmax(Corr_Vector)]
    Shape_Corr = np.max(Corr_Vector)
    Shape_Angle = Angle_Vector[np.argmax(Corr_Vector)]
    return Shape_Name,Shape_Corr, Shape_Angle
    
#def QR_Extractor(Image):
    #To be constructed
    #http://stackoverflow.com/questions/27233351/how-to-decode-a-qr-code-image-in-preferably-pure-python
    #qr = qrtools.QR()
    #qr.decode(Image)
    #Code = qr.data
    #return Code
def Target_Flow (Image,Shape_Name_DB_Path,Shape_DB_Path,Letter_Name_DB_Path,Letter_DB_Path):
    #This function is for the main target ID flow!
    
    #Extract primary contour from image
    Contours,Error_Code = Contour_Extractor_2(Image)
    if (Error_Code == -1):
        return 'Not a target\\Crop too noisy','NAN',-1,'NAN',-1,-1
    
    #Extract target shape
    Possible_Target_Shape,Shape_Corr_Value = Target_Shape_Extractor(Image,Contours,Shape_Name_DB_Path,Shape_DB_Path)
    
    #Extract target & letter color
    Target_Color,Letter_Color,Target_Color_Name,Letter_Color_Name = Color_Extractor(Image,Contours)
    
    #Extract letter shape & angle
    Possible_Target_Letter,Letter_Corr_Value,Letter_Angle = Letter_Extractor(Image,Contours,Letter_Name_DB_Path,Letter_DB_Path,Letter_Color)

    return 'Is Target',Possible_Target_Shape,Target_Color_Name,Possible_Target_Letter,Letter_Color_Name,Letter_Angle
    


#BUGS:
#4. Need to add failure criteria & filtering options in the code for the user.
#5. Bug when no letter is detected, algorithm continues and gets an error.
#7. Correct contour sizes to actual ones (smaller)
#8. Add QR code recognition