import os

#
# Paths and Folders
#
AUVSI_BASE_FOLDER = os.path.expanduser('~/.auvsi')
IMAGES_FOLDER = os.path.join(AUVSI_BASE_FOLDER, 'images')
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
CHDKPTP_PATH = os.path.expanduser('~/code/chdkptp/chdkptp-sample.sh')