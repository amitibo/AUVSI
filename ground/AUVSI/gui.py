#install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

import server

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSidebar
from kivy.properties import ObjectProperty
import pkg_resources
import global_settings as gs
from configobj import ConfigObj
import os

from settingsjson import network_json, camera_json


class BGLabel(Label):
    pass


class ImagesList(BoxLayout):
    pass


class ImageProcessingGui(BoxLayout):
    connect_state = ObjectProperty()
    
    def shoot(self, state):
        server.access('camera='+('on' if state else 'off'))
        
        
# A simple kivy App, with a textbox to enter messages, and
# a large label to display all the messages received from
# the server
class GUIApp(App):
    kv_directory = pkg_resources.resource_filename('AUVSI', 'resources')
    connection = None
    
    def build(self):
        self.settings_cls = SettingsWithSidebar
        self.connect_to_server()
        
    def build_config(self, config):
        config.setdefaults(
            'Network', {'IP': '192.168.1.16', 'port': 8000}
            )
        config.setdefaults(
            'Camera', {'ISO': 100, 'Shutter': 5000, 'Aperture': 4, 'Zoom': 45}
        )
    
    def build_settings(self, settings):
        settings.add_json_panel("Network", self.config, data=network_json)
        settings.add_json_panel("Camera", self.config, data=camera_json)
    
    def on_config_change(self, config, section, key, value):
        if section == 'Network':
            self.connect_to_server()
            
    def connect_to_server(self):
        server.setserver(
            ip=self.config.get('Network', 'ip'),
            port=self.config.getint('Network', 'port')
        )
        server.connect(self)

    def on_connection(self, connection):
        self.root.connect_state.canvas.before.children[0].rgb = (0, 0, 1)
        self.root.connect_state.text = 'Connected'
        self.connection = connection
        
    def on_disconnection(self, connection):
        self.root.connect_state.canvas.before.children[0].rgb = (1, 0, 0)
        self.root.connect_state.text = 'Disconnected'
        self.connection = None

    def send_message(self, *args):
        msg = self.textbox.text
        if msg and self.connection:
            self.connection.write(str(self.textbox.text))
            self.textbox.text = ""

    def print_message(self, msg):
        #self.label.text += msg + "\n"
        print msg
    
    def get_images(self):
        pass
    
    
if __name__ == '__main__':
    GUIApp().run()
