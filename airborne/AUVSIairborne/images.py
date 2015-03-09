from __future__ import division
import exifread
import cv2


def handleNewImage(img_path):
    #
    # Create the image processing pipeline
    #
    #
    # Get some data from the EXIF
    #
    with open(img_path, 'rb') as f:
        tags = exifread.process_file(f)

    #
    # Calculate camera intrinsic matrix.
    #
    in_to_mm = 25.4
    FocalPlaneYResolution = tagRatio(tags['EXIF FocalPlaneYResolution'])
    FocalPlaneXResolution = tagRatio(tags['EXIF FocalPlaneXResolution'])
    