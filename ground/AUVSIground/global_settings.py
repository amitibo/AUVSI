from datetime import datetime
import os

BASE_TIMESTAMP = '%Y_%m_%d_%H_%M_%S_%f'

#
# Paths and Folders
#
AUVSI_BASE_FOLDER = os.path.join(os.path.expanduser('~/.auvsi_ground'), datetime.now().strftime(BASE_TIMESTAMP))
IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'images')
DB_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'db')
DB_PATH = os.path.join(DB_FOLDER, 'auvsi.db')

#
# Database data
#
IMAGES_TABLE = 'images_table'
