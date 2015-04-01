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
from functools import partial
import numpy as np
import AUVSIcv.transformation_matrices as TM
import AUVSIground.global_settings as gs
import pandas as pd
from AUVSIcv import NED
import AUVSIcv
import glob
import time
import math
import os


class Map(Scatter):
    do_rotation=False

    def redraw(self, index):
        
        self.canvas.clear()
        with self.canvas:
            for i, quad in enumerate(quads):
                if i == index:
                    Color(1, 1, 1, 1, mode='rgba')
                else:
                    Color(1, 1, 1, 0.1, mode='rgba')
                    
                points = tuple(quad.T[...,:2].flatten()+100)
                Quad(source=imgs[i].path, points=points)
            
    
class CanvasApp(App):

    quad_index = 0
    clock_trigger = None
    
    def setMapIndex(self, map_widget, delta, *largs):
        self.quad_index += delta
        self.quad_index = self.quad_index % len(quads)
        
        map_widget.redraw(index=self.quad_index)
        #if self.clock_trigger is not None:
            #self.clock_trigger.cancel()
        
        #time.sleep(0.2)
        #self.clock_trigger = Clock.create_trigger(partial(self.setMapIndex, map_widget, delta))
        #self.clock_trigger()
    
    def build(self):
        
        map_widget = Map()
        map_widget.size=[3000, 3000]
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
    
    TIME_OFFSET = 1
    base_path = gs.IMAGES_FOLDER
    imgs_paths = sorted(glob.glob(os.path.join(base_path, '*0.jpg')))
    data_paths = [os.path.splitext(path)[0]+'.json' for path in imgs_paths]
    imgs_paths = sorted(glob.glob(os.path.join(base_path, '*tn.jpg')))
    
    imgs = [AUVSIcv.Image(img_path, data_path) for img_path, data_path in zip(imgs_paths[TIME_OFFSET:], data_paths[:-TIME_OFFSET])]
    ned = NED.NED(imgs[0].latitude, imgs[0].longitude, 0)
    
    quads = [
        img.calculateQuad(ned, resolution=[4000, 3000]) for img in imgs
    ]
    
    CanvasApp().run()
