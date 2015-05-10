__author__ = 'Ori'

from AUVSIcv.Mser_Color_Scaled_Down import MSER_Primary
import cv2


image = cv2.imread(
    r"C:\Users\Ori\Downloads\Telegram Desktop\target.jpg")

cv2.imshow("Input Image", image)
cv2.waitKey(0)

image_info = {'Focal_Length': 4, 'Flight_Altitude': 10}
mser_results = MSER_Primary(image, image_info, 1, None)
print(mser_results)