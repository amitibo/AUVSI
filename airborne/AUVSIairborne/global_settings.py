import os
import warnings
from datetime import datetime

BASE_TIMESTAMP = '%Y_%m_%d_%H_%M_%S_%f'

#
# Paths and Folders
#
AUVSI_BASE_FOLDER = os.path.join(os.path.expanduser('~/.auvsi_airborne'), datetime.now().strftime(BASE_TIMESTAMP))
IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'images')
RENAMED_IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'renamed_images')
RESIZED_IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'resized_images')
FLIGHT_DATA_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'flight_data')
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
