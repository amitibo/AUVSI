"""
"""

from __future__ import division
import numpy as np

__all__ = (
    'lla2ecef',
)


def lla2ecef(latitude, longitude, altitude):
    """
    Convert between latitude, longitude and altitude to meters.
    Note:
    -----
    The conversion is done so that x points to the North, y points to the east and z points up.
    """

    x = latitude * 60 * 1609.34
    y = -longitude * 60 * 1609.34 * np.cos(latitude*np.pi/180)

    return x, y, altitude


