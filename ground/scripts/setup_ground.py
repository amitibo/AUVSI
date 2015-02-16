from AUVSI import global_settings as gs
from configobj import ConfigObj
import pkg_resources
import os
import shutil


def main():
    #
    # Create the base folder.
    #
    if not os.path.exists(gs.AUVSI_BASE_FOLDER):
        os.makedirs(gs.AUVSI_BASE_FOLDER)

if __name__ == '__main__':
    main()