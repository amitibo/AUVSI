AUVSI Image Processing Software
===============================

The AUVSI Image Procssing Software contains the software developed for the AUVSI competition
for the image processing tasks. It is made of three parts, the code run on the airborne computer,
the code that runs on the ground station and a separate project for development and testing of
image processing algorithms. The software is written in python.

The AUVSI project (2015) makes use of two platforms, the airborne computer is an ODROID XU3.
The other platform is a windows computer which runs the ground station.

Airborne platform
-----------------
The airborne platform used in 2015 competition is the ODROID XU3 running xubunutu 14.04.

### Prerequisits

* screen
* mercurial
* python
* opencv
* twisted
* sortedcontainers: Install with 'pip install sortedcontainers'
* chdkptp - The communication with the Cannon camera (used in 2015) is done using the chdkptp code.

###### Installing chdkptp

* Can be downloaded form: https://github.com/tudelft/chdkptp
* Install (on ODROID) using the following link: http://chdk.wikia.com/wiki/Getting_CHDKPTP_on_BeagleBone_Black_to_work Note that instead of lua5.1 it should be lua5.2 also there is a small typo in the name of libusb-1.0-0-dev
* Follow the following links to deactivate gphoto2 (It seems to grab the camera before chdkptp): http://chdk.setepontos.com/index.php?topic=10664.10 http://chdk.setepontos.com/index.php?topic=6231.msg100671#msg100671
* Important to run from the lua folder (or update the chdkptp-sample.sh to point to the chdkptp executable).
* Important to run as sudo!!!
* Last years cofigurations: http://chdk.setepontos.com/index.php?topic=11142.0 http://libptp.sourceforge.net/README
* Maybe someday useful: https://pypi.python.org/pypi/pyptpchdk/0.2.1

To use the camera in mode simulation, the following should also be installed:

* freetype - Install using 'sudo apt-get install libfreetype6'
* aggdraw - Install from source (preferably from svn) set the variable FREETYPE_ROOT = "/usr/" in the setup.py file.
* PIL
* exifread: Install with 'pip install exifread'
* pyqrcode: Install with 'pip install pyqrcode'
* pypng: Install with 'pip install pypng'

### Installation

    > hg clone ...
    > cd auvis/airborne
    > python setup.py install
    > cp rc.local /etc/rc.local

Ground platform and Image Processing project
--------------------------------------------

### Prerequisits

* mercurial: Install using TortoiseHg
* Anaconda (+accelerate). Works with python >= 2.7.8 (due to a bug: http://bugs.python.org/issue21652)
* twisted: Install using 'conda install twisted'
* opencv: Install from 'Unofficial python binaries'. Tested with version >= 2.4.10
* pygame: Install from 'Unofficial python binaries'.
* kivy: Install from 'Unofficial python binaries'.
* aggdraw (used for the image processing project): Install from 'Unofficial python binaries'.
* exifread: Install with 'pip install exifread'
* pyqrcode: Install with 'pip install pyqrcode'
* pypng: Install with 'pip install pypng'

### Installation

    > hg clone ...
    > cd auvis/ground
    > python setup.py develop
    > cd ../image_processing
    > python setup.py develop

Setup
-----
1. Prepare and install an CHDK SD for the Cannon camera.
2. Connect the Canon camera to the ODROID XU3.
3. Setup the network: the ground station communicates with airborne computer through a router
   (this is done in order to avoid the need to setup a static IP). Find the IP of the airborne
   platform, can be done directly
4. Download some drone images (size 4000x3000) to some folder and create the 'AUVSI_CV_DATA'
   environment variable and set it to this folder path. This is used by the image_processing
   project and the simulation camera.
  
  
