from __future__ import division
import AUVSIcv
import numpy as np
import cv2
import glob
import os
import time
import json
from scipy import ndimage
import matplotlib.pyplot as plt

#base_path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Shapes'

base_path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Letters'
imgs_paths = sorted(glob.glob(os.path.join(base_path, '*.png')))
Contour_Vector_Length = 500
Shape_Num = len(imgs_paths)
Contour_Matrix = np.zeros([Shape_Num,Contour_Vector_Length],np.complex128)
Contour_Name_Array = ["" for x in range(Shape_Num)]

#''''
#cv2.namedWindow('3',flags=cv2.WINDOW_NORMAL)
#cv2.imshow('3',Binary_Image)
#cv2.waitKey(0)
#''''
#plt.plot(Short_X,Short_Y)
#plt.show()
for i in range(Shape_Num):
    Image = cv2.imread(imgs_paths[i])
    Contour_Name_Array[i] = os.path.basename(imgs_paths[i])
    Gray_Image = cv2.cvtColor(Image,cv2.COLOR_RGB2GRAY)
    Unused_2,Binary_Image = cv2.threshold(Gray_Image, 200, 255,0)
    Contours,Unused_1 = cv2.findContours(np.invert(Binary_Image.copy()), cv2.RETR_TREE, cv2.CHAIN_APPROX_NONE)
    Cont_X = np.zeros([len(Contours[0])],np.uint8)
    Cont_Y = np.zeros([len(Contours[0])],np.uint8)
    for j in range(len(Contours[0])):
        Cont_X[j] = Contours[0][j][0][0]
        Cont_Y[j] = Contours[0][j][0][1]
    
    Ratio = Contour_Vector_Length/len(Cont_X)  
    Short_X = ndimage.interpolation.zoom(np.float32(Cont_X),Ratio)
    Short_Y = ndimage.interpolation.zoom(np.float32(Cont_Y),Ratio)
        #final = np.vstack((a,b)).T        
    #plt.plot(Short_X,Short_Y)
    #plt.show()    
    Vector_Size = len(Short_X)
    Short_X = np.float32(Short_X)
    Short_Y = np.float32(Short_Y)
    #Gamma_Vector = np.zeros([Vector_Size,1],np.complex128)
    for k in range(Vector_Size):
        if (k == Vector_Size - 1):
            Contour_Matrix[i][k] = (Short_X[0]-Short_X[k]) + (Short_Y[0]-Short_Y[k])*1j
        else:
            Contour_Matrix[i][k] = (Short_X[k+1]-Short_X[k]) + (Short_Y[k+1]-Short_Y[k])*1j
    Norm = np.sqrt(sum(pow(np.absolute(Contour_Matrix[i]),2)))
    #Norm = np.sqrt(abs(np.dot(Contour_Matrix[i],Contour_Matrix[i])))
    Contour_Matrix[i] = Contour_Matrix[i]/Norm
Output_Path_1 = base_path + '\\' + 'Contour_DB'
np.save(Output_Path_1,Contour_Matrix)
Output_Path_2 = base_path + '\\' + 'Contour_Name_DB'
np.save(Output_Path_2,Contour_Name_Array) #,delimiter=" ",fmt="%s"

