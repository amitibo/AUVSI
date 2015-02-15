from AUVSI import global_settings as gs
from configobj import ConfigObj
import pkg_resources
import os
import shutil


def main():
    #
    # Create an initial config file.
    #
    if not os.path.exists(gs.AUVSI_BASE_FOLDER):
        os.makedirs(gs.AUVSI_BASE_FOLDER)
        
    shutil.copy(pkg_resources.resource_filename('AUVSI', 'resources/settings.ini'), gs.CONFIG_PATH)


if __name__ == '__main__':
    main()