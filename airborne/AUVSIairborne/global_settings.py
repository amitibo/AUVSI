import os
import warnings

#
# Paths and Folders
#
AUVSI_BASE_FOLDER = os.path.expanduser('~/.auvsi_airborne')
IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'images')
RESIZED_IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'resized_images')
DB_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'db')
DB_PATH = os.path.join(DB_FOLDER, 'auvsi.db')

#
# Database data
#
IMAGES_TABLE = 'images_table'

#
# Camera data
#
BASE_ZOOM = 0
try:
    CHDKPTP_PATH = os.path.join(os.environ['CHDKPTP_DIR'], 'chdkptp-sample.sh')
except:
    warnings.warn('CHDKPTP_PATH env variable not found.')