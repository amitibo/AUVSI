
class UnknownCommand(Exception):
    pass

# Create database folders
import os
import global_settings as gs

try:
    os.makedirs(gs.IMAGES_FOLDER)
except:
    pass

try:
    os.makedirs(gs.FLIGHT_DATA_FOLDER)
except:
    pass

try:
    os.makedirs(gs.IMAGES_DATA)
except:
    pass

try:
    os.makedirs(gs.RESIZED_IMAGES_FOLDER)
except:
    pass

