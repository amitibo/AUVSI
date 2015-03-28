'''
Canvas stress
=============

This is just a test for testing the performance of our Graphics engine.
'''

from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.app import App
from kivy.graphics import Color, Rectangle, Quad
from kivy.uix.scatter import Scatter
from kivy.clock import Clock
from random import random as r
from functools import partial
import numpy as np
import AUVSIcv.transformation_matrices as TM
import pandas as pd
from AUVSIcv import NED
import AUVSIcv
import os

def loadData(path):
    
    data = pd.read_csv(path)
    lat, lon, alt, yaw = [data[field].values for field in ['lat', 'lon', 'alt', 'yaw']]
    
    ned = NED.NED(lat[0], lon[0], 0)
    x, y, h = [np.array(val) for val in zip(*[ned.geodetic2ned([la, lo, al]) for la, lo, al in zip(lat, lon, alt)])]
    
    #
    # We need to make the coords positive. Also in the NED coords, z axis (h) points into the ground.
    #
    x = x - x.min()
    y = y - y.min()
    h = -h
    
    return x, y, h, yaw


def calculateQuad(center, yaw, Kinv, resolution):
    
    points = np.array(((0, resolution[0], resolution[0], 0), (0, 0, resolution[1], resolution[1]), (1, 1, 1, 1.)))
    Ryaw = TM.euler_matrix(0, 0, np.deg2rad(-yaw), axes='sxyz')
    h = center[2]
    offset = np.array(((center[0],), (center[1],), (h,)))
    
    projections = offset + h * np.dot(np.array(((1., 0, 0), (0, 1, 0), (0, 0, -1.))), np.dot(Ryaw[:3, :3], np.dot(Kinv, points)))
    
    return projections
    
    
class Map(Scatter):
    do_rotation=False
    
    def redraw(self, index):
        
        self.canvas.clear()
        with self.canvas:
            for i, quad in enumerate(quads):
                if i == index:
                    Color(1, 1, 1, 1, mode='rgba')
                else:
                    Color(1, 1, 1, 0.01, mode='rgba')
                    
                points = tuple(quad.T[...,:2].flatten())
                Quad(source=img.path, points=points)
            
    
class CanvasApp(App):

    quad_index = 0
    clock_trigger = None
    
    def setMapIndex(self, map_widget, delta, *largs):
        self.quad_index += delta
        self.quad_index = self.quad_index % len(quads)
        
        map_widget.redraw(index=self.quad_index)
        if self.clock_trigger is not None:
            self.clock_trigger.cancel()
        
        self.clock_trigger = Clock.create_trigger(partial(self.setMapIndex, map_widget, delta))
        self.clock_trigger()
    
    def build(self):
        
        map_widget = Map()
        map_widget.redraw(index=self.quad_index)
        
        btn_prev = Button(text='PREV',
                          on_press=partial(self.setMapIndex, map_widget, -1))
    
        btn_next = Button(text='NEXT',
                          on_press=partial(self.setMapIndex, map_widget, 1))
    
        layout = BoxLayout(size_hint=(1, None), height=50)
        layout.add_widget(btn_prev)
        layout.add_widget(btn_next)
    
        root = BoxLayout(orientation='vertical')
        rl = RelativeLayout()
        rl.add_widget(map_widget)
        root.add_widget(rl)
        root.add_widget(layout)

        return root






if __name__ == '__main__':
    
    x, y, h, yaw = loadData(os.path.join(os.environ['AUVSI_CV_DATA'], '49.csv'))
    #yaw = 10*np.ones_like(yaw)
    
    img = AUVSIcv.Image(os.path.join(os.environ['AUVSI_CV_DATA'], 'IMG_0411.jpg'))
    K = img.K
    Kinv = np.linalg.inv(K)
    
    SIZE = 1000
    quads = [calculateQuad((_y, _x, _h), yaw, Kinv, resolution=[4000, 3000]) for _x, _y, _h, yaw in zip(x[:SIZE], y[:SIZE], h[:SIZE], yaw[:SIZE])]
    
    CanvasApp().run()
