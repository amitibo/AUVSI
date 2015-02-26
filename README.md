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

Prerequisits
------------
screen
mercurial
python
opencv
twisted
chdkptp - The communication with the Cannon camera (used in 2015) is done using the chdkptp code.

Installation
------------
> hg clone ...
> cd auvis/airborne
> python setup.py install
> cp rc.local /etc/rc.local

Ground platform and Image Processing project
--------------------------------------------

Prerequisits
------------
mercurial
Anaconda (+accelerate)
opencv
pygame
kivy
aggdraw (used for the image processing project)

Installation
------------
> hg clone ...
> cd auvis/ground
> python setup.py develop
> cd ../image_processing
> python setup.py develop

Setup
-----
- Prepare and install an CHDK SD for the Cannon camera.
- Connect the Canon camera to the ODROID XU3.
- Setup the network: the ground station communicates with airborne computer through a router
  (this is done in order to avoid the need to setup a static IP). Find the IP of the airborne
  platform, can be done directly
  