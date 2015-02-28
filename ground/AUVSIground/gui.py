#install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

import server

from twisted.python import log
from twisted.python.logfile import DailyLogFile

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSidebar
from kivy.properties import ObjectProperty
from kivy.uix.stencilview import StencilView
from kivy.uix.button import Button

import pkg_resources
import global_settings as gs
from configobj import ConfigObj
import os

from settingsjson import network_json, camera_json, admin_json


class BGLabel(Label):
    pass


class BoxStencil(BoxLayout, StencilView):
    pass


class ImagesGalleryWin(BoxLayout):
    scatter_image = ObjectProperty()
    stacked_layout = ObjectProperty()


class ImageProcessingGui(BoxLayout):
    connect_label = ObjectProperty()
    images_gallery = ObjectProperty()
    
    def build(self, *params):
        pass
    
    def shoot(self, start_shooting):
        if start_shooting:
            server.access('camera_on')
        else:
            server.access('camera_off')
        
        
class GUIApp(App):
    """Main AUVSI ground system application."""
    
    kv_directory = pkg_resources.resource_filename('AUVSIground', 'resources')
    connection = None
    
    def build(self):
        """Main build function of the Kivy application."""
        
        #
        # Setup logging.
        #
        if not os.path.exists(gs.AUVSI_BASE_FOLDER):
            os.makedirs(gs.AUVSI_BASE_FOLDER)
        
        f = DailyLogFile('server.log', self.config.get('Admin', 'logging path'))
        log.startLogging(f)
        
        self.settings_cls = SettingsWithSidebar
        
        #
        # Start up the local server.
        #
        self.connect_to_server()
        
        #
        # Synchronize the image database.
        #
        self.populateImagesList()
        
    def _populateImagesList(self, images_list):
        """Store new image paths in image list."""

        def callback(instance):
            self.root.images_gallery.scatter_image.source = instance.background_normal
    
        for image_path in images_list:
            btn = Button(
                size_hint=(None, None),
                size=(100, 100),
                background_normal=image_path,
                border=(0,0,0,0)
            )
    
            btn.bind(on_press=callback)
            self.root.images_gallery.stacked_layout.add_widget(btn)        

        
    def populateImagesList(self):
        """Populate the images list from the database."""
        
        self._gui_server.getImagesList(self._populateImagesList)
        
    def build_config(self, config):
        """Create the default config (used the first time the application is run)"""
        
        config.setdefaults(
            'Network', {'IP': '192.168.1.16', 'port': 8000}
            )
        config.setdefaults(
            'Camera', {'ISO': 100, 'Shutter': 5000, 'Aperture': 4, 'Zoom': 45}
        )
        config.setdefaults(
            'Admin', {'Logging Path': gs.AUVSI_BASE_FOLDER}
        )
    
    def build_settings(self, settings):
        """Build the settings menu."""
        
        settings.add_json_panel("Network", self.config, data=network_json)
        settings.add_json_panel("Camera", self.config, data=camera_json)
        settings.add_json_panel("Admin", self.config, data=admin_json)
    
    def on_config_change(self, config, section, key, value):
        """Handle change in the settings."""
        
        if section == 'Network':
            self.connect_to_server()
        elif section == 'Camera':
            args = {
                'ISO': self.config.get('Camera', 'iso'),
                'shutter': self.config.get('Camera', 'shutter'),
                'aperture': self.config.get('Camera', 'aperture'),
                'zoom': self.config.get('Camera', 'zoom'),
            }
            server.access('camera_set', args=args)
            
    def connect_to_server(self):
        """Initiate connection to airborne server."""
        
        server.setserver(
            ip=self.config.get('Network', 'ip'),
            port=self.config.getint('Network', 'port')
        )
        self._gui_server = server.connect(self)

    def on_connection(self, connection):
        """Callback on successfull connection to the server."""
        
        self.root.connect_label.canvas.before.children[0].rgb = (0, 0, 1)
        self.root.connect_label.text = 'Connected'
        self.connection = connection
        
    def on_disconnection(self, connection):
        """Callback on disconnection from the server."""

        self.root.connect_label.canvas.before.children[0].rgb = (1, 0, 0)
        self.root.connect_label.text = 'Disconnected'
        self.connection = None

    def log_message(self, msg):
        """"""
        
        log.msg(msg)

    
if __name__ == '__main__':
    GUIApp().run()
