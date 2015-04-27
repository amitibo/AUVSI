from mapview import MapView, MapSource, MapMarker
from kivy.base import runTouchApp
import pkg_resources
import os


icons_folder = pkg_resources.resource_filename('AUVSIobstacles', 'resources')

kwargs = {'zoom': 15, 'lon': 35.094502, 'lat': 32.95119}

map = MapView(**kwargs)
m1 = MapMarker(lon=35.094502, lat=32.95119, source=os.path.join(icons_folder, 'airplane.png'))
map.add_marker(m1)
runTouchApp(map)
