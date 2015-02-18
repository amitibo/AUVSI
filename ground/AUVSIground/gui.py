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
from kivy.uix.image import Image

import pkg_resources
import global_settings as gs
from configobj import ConfigObj
import os

from settingsjson import network_json, camera_json


class BGLabel(Label):
    pass


class ImagesForm(BoxLayout):
    image_viewer = ObjectProperty()
    images_names = ObjectProperty()
    
    def __init__(self, **kwargs):
        super(ImagesForm, self).__init__(**kwargs)

        #self.listview.adapter.bind(
            #on_selection_change=self.imageviewer.image_changed
        #)

        

class ImageViewer(BoxLayout):
    def __init__(self, **kwargs):
        kwargs['orientation'] = 'vertical'
        self.image_path = kwargs.get('image_path', '')
        super(ImageViewer, self).__init__(**kwargs)
        if self.image_path:
            self.redraw()

    def redraw(self, *args):
        self.clear_widgets()

        if self.image_path:
            self.add_widget(
                Image(
                    self.image_path
                )
            )

    def image_changed(self, list_adapter, *args):
        if len(list_adapter.selection) == 0:
            self.image_path = None
        else:
            selected_object = list_adapter.selection[0]

            # [TODO] Would we want touch events for the composite, as well as
            #        the components? Just the components? Just the composite?
            #
            # Is selected_object an instance of ThumbnailedListItem (composite)?
            #
            # Or is it a ListItemButton?
            #
            if hasattr(selected_object, 'fruit_name'):
                self.image_path = selected_object.fruit_name
            else:
                self.image_path = selected_object.text

        self.redraw()


class ImageProcessingGui(BoxLayout):
    connect_label = ObjectProperty()
    
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
        
        self.settings_cls = SettingsWithSidebar
        self.connect_to_server()
        self.populateImagesList()
    
    def _populateImagesList(self, images_list):
        """"""
        
        images_list = [os.path.split(items[0])[1] for items in images_list]
        
        items = self.root.images_form.images_names.adapter.data
        [items.append(item) for item in images_list]
        
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
    
    def build_settings(self, settings):
        """Build the settings menu."""
        
        settings.add_json_panel("Network", self.config, data=network_json)
        settings.add_json_panel("Camera", self.config, data=camera_json)
    
    def on_config_change(self, config, section, key, value):
        """Handle change in the settings."""
        
        if section == 'Network':
            self.connect_to_server()
            
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

    def print_message(self, msg):
        """Debug print (Maybe should be removed when better logging is implementd)."""
        print msg

    
if __name__ == '__main__':
    GUIApp().run()
