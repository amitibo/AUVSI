from AUVSIcv import Target_ID
import cv2

Crop_Path = 'C:\Users\sbousche\Documents\AUVSI Images\Full Res Crops\Crop No.50.jpg'
Image = cv2.imread(Crop_Path)

Shape_DB_Path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Shapes\Contour_DB.npy'
Shape_Name_DB_Path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Shapes\Contour_Name_DB.npy'
Letter_DB_Path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Letters\Contour_DB.npy'
Letter_Name_DB_Path = 'C:\Users\sbousche\Documents\AUVSI\image_processing\AUVSIcv\Contours\Letters\Contour_Name_DB.npy'

Is_Target,Possible_Target_Shape,Target_Color,Possible_Target_Letter,Letter_Color,Letter_Angle = Target_ID.Target_Flow(Image,Shape_Name_DB_Path,Shape_DB_Path,Letter_Name_DB_Path,Letter_DB_Path)

a = 1