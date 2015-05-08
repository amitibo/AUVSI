import os
import warnings

#
# Paths and Folders
#
AUVSI_BASE_FOLDER = os.path.expanduser('~/.auvsi_airborne')
IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'images')
RENAMED_IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'renamed_images')
RESIZED_IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'resized_images')
FLIGHT_DATA_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'flight_data')
DB_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'db')
DB_PATH = os.path.join(DB_FOLDER, 'auvsi.db')

#
# Ftp connection details
#
FTP = {'user': 'auvsi', 'pass': '1234'}

#
# Performance
#
LOW_RES_SYNC_TIME = 1

#
# Camera data
#
BASE_ZOOM = 0
try:
    CHDKPTP_PATH = os.path.join(os.environ['CHDKPTP_DIR'], 'chdkptp-sample.sh')
except:
    warnings.warn('CHDKPTP_PATH env variable not found.')
