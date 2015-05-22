__author__ = 'Ori'
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from widgets import *

from kivy.app import App
from kivy.uix.settings import SettingsWithSidebar
from kivy.properties import ObjectProperty
from kivy.uix.button import Button
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
import pkg_resources
#import global_settings as gs
from configobj import ConfigObj

from random import random
from math import sqrt


class DetectionEntry(BoxLayout):
    # detection_data_path = StringProperty('default')
    pass


class AutoDetectionScreen(Screen):
    def auto_detect(self):
        entry = DetectionEntry()
        entry.detection_data_path = 'Hi'
        self.ids.entry_container.add_widget(entry)
        print(self.ids.entry_container)


class ManualDetectionScreen(Screen):
    pass



class MyScreenManager(ScreenManager):
    pass
