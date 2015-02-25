#install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

import server

from twisted.python import log
from twisted.python.logfile import DailyLogFile

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.settings import SettingsWithSidebar
from kivy.properties import ObjectProperty
from kivy.uix.listview import ListView, ListItemButton
from kivy.uix.image import Image

import pkg_resources
import global_settings as gs
from configobj import ConfigObj
import os

from settingsjson import network_json, camera_json, admin_json


class BGLabel(Label):
    pass


class ImagesListView(ListView):
    pass


class ImageViewer(BoxLayout):
    def __init__(self, **kwargs):
        super(ImageViewer, self).__init__(**kwargs)

        kwargs['orientation'] = 'vertical'
        self.image_path = kwargs.get('image_path', r'')

        if self.image_path:
            self.redraw()

    def redraw(self, *args):
        self.clear_widgets()

        if self.image_path:
            self.add_widget(
                Image(
                    source=self.image_path
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
            if hasattr(selected_object, 'img_path'):
                self.image_path = selected_object.fruit_name
            else:
                self.image_path = selected_object.text

        self.redraw()


class ImagesForm(BoxLayout):
    image_viewer = ObjectProperty()
    images_names = ObjectProperty()
    
    def __init__(self, **kwargs):
        super(ImagesForm, self).__init__(**kwargs)


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
        
        #
        # Setup logging.
        #
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
        
        #
        # I do the binding here because in the __init__ of ImagesForm 
        # the adapter of the list is still not working.
        #
        self.root.images_form.images_names.adapter.bind(
            on_selection_change=self.root.images_form.image_viewer.image_changed
        )

    
    def _populateImagesList(self, images_list):
        """Store new image paths in image list."""

        items = self.root.images_form.images_names.adapter.data
        [items.append(item) for item in images_list]
        self.root.images_form.images_names._trigger_reset_populate() 
        
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
            pass
            
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
