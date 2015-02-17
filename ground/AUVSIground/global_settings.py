import os

#
# Paths and Folders
#
AUVSI_BASE_FOLDER = os.path.expanduser('~/.auvsi_ground')
IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'images')
DB_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'db')
DB_PATH = os.path.join(DB_FOLDER, 'auvsi.db')
CONFIG_PATH = os.path.join(AUVSI_BASE_FOLDER, 'settings.ini')

#
# Database data
#
IMAGES_TABLE = 'images_table'
