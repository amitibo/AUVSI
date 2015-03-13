# -*- coding: latin-1 -*-
"""
MSER Code
Code description:
The code recives an image, an dict type strucure with details
of the image (focal length, flight altitude, camera angles etc.),
a scaling constant and returns a scaled down image, an array of
crops (images) from the original image and a dict type structure with
relevant data for each crop (size, location relative to the original 
image etc.). The image data is structured as follows:
Image_Information = {'Focal_Length': Number, 'Flight_Altitude': Number, 'Camera_Pitch_Angle': Number, 'Camera_Roll_Angle' : Number}

Author: Shlomi Bouscher
Version: 0.1.0
Date: 03/03/2015
"""

import cv2
import numpy as np
import Image


def targetsUnifier(Crop_Data):
    """"""
    
    Error_Code = 0
    Error_String = 'None'

    New_Crop_Data = Crop_Data

    for i in range(0,len(New_Crop_Data)):

        Current_Crop = New_Crop_Data[i]
        Orig_Location_X = Current_Crop[0]
        Orig_Location_Y = Current_Crop[1]

        if ((Orig_Location_X != -1) and (Orig_Location_Y != -1)):
            for j in range(0,len(New_Crop_Data)):

                Current_Crop_2 = New_Crop_Data[j]
                Location_Coord_X = Current_Crop_2[0]
                Location_Coord_Y = Current_Crop_2[1]

                if ((Location_Coord_X != -1) and (Location_Coord_Y != -1) and (i != j)):

                    X_Max = Current_Crop[2]
                    X_Min = Current_Crop[3]
                    Y_Max = Current_Crop[4]
                    Y_Min = Current_Crop[5]

                    if ((Location_Coord_X > X_Min) and (Location_Coord_X < X_Max) and (Location_Coord_Y> Y_Min) and (Location_Coord_Y < Y_Max)):

                        Current_Crop_2[0] = -1
                        Current_Crop_2[1] = -1
                        X_Max_2 = Current_Crop_2[2]
                        X_Min_2 = Current_Crop_2[3]
                        Y_Max_2 = Current_Crop_2[4]
                        Y_Min_2 = Current_Crop_2[5]

                        if (X_Max_2 > X_Max):

                            Current_Crop[2] = X_Max_2

                        if (X_Min_2 < X_Min):

                            Current_Crop[3] = X_Min_2

                        if (Y_Max_2 > Y_Max):

                            Current_Crop[4] = Y_Max_2

                        if (Y_Min_2 < Y_Min):

                            Current_Crop[5] = Y_Min_2

                        New_Crop_Data[j] = Current_Crop_2
                        New_Crop_Data[i] = Current_Crop

    return (New_Crop_Data,Error_Code,Error_String)


def MSER_primary(Image,Image_Information,Scaling_Constant,Crop_Save_Path):
    """Primary airborne image processing function"""

    #
    # Acquire competition data (targets, camera spec etc.)
    # 
    Competition_Data_Block = competitionData()

    #
    # Define a safety gap with croping segments of the image
    #
    Crop_Safety_Gap = 10
    
    #
    # Obtain minimum & maximum target size in pixel number
    #
    Target_Size = list(targetSizeGenerator(Image_Information,Competition_Data_Block,Scaling_Constant))
    Resized_Image = cv2.resize(Image, (0,0), fx = Scaling_Constant, fy = Scaling_Constant)    
    
    MSER_Result = dynamicMSER(Resized_Image,Image_Information,Target_Size)

    Error_Code = MSER_Result[1]
    Crops = MSER_Result[0]
    #Crop_Data = [0]*len(Crops)
    Crop_Data = []
   
    if Error_Code == 0: 
        for i in range(0,len(Crops)):
            Temp = list(cropMinMaxCenter(Crops[i],Crop_Safety_Gap,Scaling_Constant))
            Crop_Data.append(Temp)

        New_Crop_Data = targetsUnifier(Crop_Data)
        New_Crop_Data_2 = New_Crop_Data[0]
        imageCrop(Image,New_Crop_Data_2,Crop_Save_Path)
    scaleImage(Image,Crop_Save_Path,Scaling_Constant)
    
    
def imageCrop(Image,Crop_Data,Crop_Save_Path):
    """
    Known_Issues
    ------------
    1. Might have problems with crop boundries out of range, but crop function
       can handle it (tested).
    """
    
    for i in range(0,len(Crop_Data)):

        Current_Crop = Crop_Data[i]
        Location_X = Current_Crop[0]
        Location_Y = Current_Crop[1]

        if ((Location_X != -1) and (Location_Y != -1)):   

            X_Max = Current_Crop[2]
            X_Min = Current_Crop[3]
            Y_Max = Current_Crop[4]
            Y_Min = Current_Crop[5]

            Crop = Image[Y_Min:Y_Max, X_Min:X_Max]
            cv2.imwrite(Crop_Save_Path + '\\' + 'Crop No.' + str(i) + '.jpg',Crop)     


def dynamicMSER(Image,Image_Information,Target_Size):
    """Returns a dict object containing the MSER regions located"""
    
    Error_Code = 0
    Error_String = 'None'

    Delta = 2
    Min_Size = int(Target_Size[0])
    Max_Size = int(Target_Size[1])
    Max_Variation = 0.05
    Min_Diversity = 0.1

    #
    # Convert Image from RGB color format to HSV color format
    #
    HSV_Image = cv2.cvtColor(Image, cv2.COLOR_BGR2HSV)                    
    Mser_Image = HSV_Image[:,:,2]
    cv2.imwrite('C:\Users\sbousche\Documents\AUVSI Images\gray_scale.png', Mser_Image)
    Mser_Object = cv2.MSER(Delta,Min_Size,Max_Size,Max_Variation,Min_Diversity)
    regions = Mser_Object.detect(Mser_Image)
    
    if (len(regions) != 0) :

        return (regions,Error_Code,Error_String)
    
    else:
        Error_Code = 1
        Error_String = 'No suspected targets were detected in this image'

    return (regions,Error_Code,Error_String)


def competitionData():
    """Returns a dict structure with relevant information"""
    
    Competition_Data = {}
    Competition_Data['Camera_Name'] = 'Canon Powershot S110'
    Competition_Data['Camera_Color_Matrix_Type'] = 'sRGB'
    Competition_Data['Camera_Dimensions'] = 'W = 98.8 [mm] , H = 59 [mm] , D = 26.9 [mm]'
    Competition_Data['Camera_Weight'] = '198' #in [g]
    Competition_Data['Camera_Focal_Distance_Min'] = 5.2 #in [mm]
    Competition_Data['Camera_Focal_Distance_Max'] = 26 #in [mm]
    Competition_Data['Camera_Focal_Length_35mm_Convert_Factor'] = 4.5
    Competition_Data['Camera_Pixel_Num_Width'] = 4000
    Competition_Data['Camera_Pixel_Num_Height'] = 3000
    Competition_Data['Camera_Sensor_Width'] = 7.6 #in [mm]
    Competition_Data['Camera_Sensor_Height'] = 5.7 #in [mm]
    Competition_Data['Camera_Sensor_Width_35mm'] = 36 #in [mm]
    Competition_Data['Camera_Sensor_Height_35mm'] = 24 #in [mm]

    #Competition_Data['Airfield_Coordinates'] = '38°09''01.5"N, 76°25''29.7"W'
    Competition_Data['Airfield_Elevation'] = 22 #in [feet]
    Competition_Data['Airfield_Magnetic_Deviation'] = 11 #in degrees to the west

    Competition_Data['Target_Max_Location_Deviation'] = 75 #in [feet]
    Competition_Data['Target_Max_Edge_Length'] = 8 #in [feet]
    Competition_Data['Target_Min_Edge_Length'] = 2 #in [feet]
    Competition_Data['Target_Max_Alphanumeric_Thickness'] = 2 #in [inch]
    Competition_Data['Target_Min_Alphanumeric_Thickness'] = 6 #in [inch]
    Competition_Data['Target_Max_Alphanumeric_Fit'] = 90 #in [%]
    Competition_Data['Target_Min_Alphanumeric_Fit'] = 50 #in [%]
    Competition_Data['Target_Max_FAR'] = 50 #in [%]
    Competition_Data['Target_Max_Targets_Detected'] = 6 #This means only 6 targets are required. There can be more out there!

    Competition_Data['QRC_Target_Max_Code_Size'] = 4 #in [feet^2]
    Competition_Data['QRC_Target_Min_Code_Size'] = 3 #in [feet^2]
    Competition_Data['QRC_Target_Max_Pixel_Size'] = 1 #in [inch^2]
    
    return Competition_Data


def targetSizeGenerator(Image_Information,Competition_Data,Scaling_Constant):
    """Creates minimum & maximum target size in pixel numbers"""
    
    Error_Code = 0
    Error_String = 'None'
    Reduction_Factor = 0.375 #From sensor size difference and target sizes (triangles are smaller by a factor of 0.5!)

    #
    # Defining relevant factors
    #
    mm_to_feet = 0.00328084 #Converting factor
    Max_Edge_Length = Competition_Data['Target_Max_Edge_Length']
    Min_Edge_Length = Competition_Data['Target_Min_Edge_Length']
    Pixel_Num_Width = Scaling_Constant*Competition_Data['Camera_Pixel_Num_Width']
    Camera_Sensor_Width_35mm = Competition_Data['Camera_Sensor_Width_35mm']
    Convert_Factor = Competition_Data['Camera_Focal_Length_35mm_Convert_Factor']
    Camera_Focal_Length = Image_Information['Focal_Length']
    Flight_Altitude = Image_Information['Flight_Altitude']
    
    #
    # Calculating 
    #
    Sensor_Width_Feet = mm_to_feet*Camera_Sensor_Width_35mm
    Feet_Per_Pixel = Sensor_Width_Feet/Pixel_Num_Width; #Same for height!
    Camera_Focal_Length_Feet_35mm = mm_to_feet*Camera_Focal_Length*Convert_Factor
    Conversation_Ratio = Camera_Focal_Length_Feet_35mm/Flight_Altitude
    Max_Edge_Length_Pixel = (Conversation_Ratio*Max_Edge_Length/Feet_Per_Pixel)
    Min_Edge_Length_Pixel = (Conversation_Ratio*Min_Edge_Length/Feet_Per_Pixel)
    Max_Target_Size = round(Max_Edge_Length_Pixel**2)
    Min_Target_Size = round(Reduction_Factor*Min_Edge_Length_Pixel**2)

    return (Min_Target_Size,Max_Target_Size,Error_Code,Error_String)


def cropMinMaxCenter(Crop_Data,Crop_Safety_Gap,Scaling_Constant):
    
    X_Max = max(a for [a,b] in Crop_Data)/Scaling_Constant + Crop_Safety_Gap
    X_Min = min(a for [a,b] in Crop_Data)/Scaling_Constant - Crop_Safety_Gap
    Y_Max = max(b for [a,b] in Crop_Data)/Scaling_Constant + Crop_Safety_Gap
    Y_Min = min(b for [a,b] in Crop_Data)/Scaling_Constant - Crop_Safety_Gap    
    X_Center = 0.5*(X_Max + X_Min)
    Y_Center = 0.5*(Y_Max + Y_Min)
    
    return (X_Center,Y_Center,X_Max,X_Min,Y_Max,Y_Min)


def scaleImage(Image,Crop_Save_Path,Scaling_Constant):
    """"""
    
    Resized_Image = cv2.resize(Image, (0,0), fx = Scaling_Constant, fy = Scaling_Constant)
    cv2.imwrite(Crop_Save_Path + '\\' + 'Scaled_Image.jpg',Resized_Image)


