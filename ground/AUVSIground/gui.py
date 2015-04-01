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
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, Point, GraphicException
from kivy.uix.image import AsyncImage
from kivy.uix.scatter import Scatter
from kivy.uix.togglebutton import ToggleButton
from kivy.core.window import Window

import pkg_resources
import global_settings as gs
import os
from random import random
from math import sqrt

from settingsjson import network_json, camera_json, cv_json, admin_json


class BGLabel(Label):
    pass


class BoxStencil(BoxLayout, StencilView):
    pass


class ScatterStencil(Scatter):
    
    def on_touch_down(self, touch):

        stencil = self.parent.parent

        #
        # Check if inside the encapsulating stencil.
        #
        if not stencil.collide_point(*self.to_window(*touch.pos)):
            return False

        return super(ScatterStencil, self).on_touch_down(touch)
    

class CoordsAction(object):
    def __init__(self, widget, touch):
        
        self._widget = widget
        win = widget.get_parent_window()
        
        self._group = str(touch.uid)

        with self._widget.canvas:
            Color(1, 1, 1, mode='hsv', group=self._group)
            self._lines = [
                Rectangle(pos=(touch.x, 0), size=(1, win.height), group=self._group),
                Rectangle(pos=(0, touch.y), size=(win.width, 1), group=self._group),
            ]
            
        self._label = Label(size_hint=(None, None))
        self.update_touch_label(touch)
        self._widget.add_widget(self._label)
 
    def on_touch_move(self, touch):
        
        self._lines[0].pos = touch.x, 0
        self._lines[1].pos = 0, touch.y

        self._label.pos = touch.pos
        self.update_touch_label(touch)
 
    def on_touch_up(self, touch):
        
        self._widget.canvas.remove_group(self._group)
        self._widget.remove_widget(self._label)

    def update_touch_label(self, touch):
        
        offset_x = self._widget.center[0]-self._widget.norm_image_size[0]/2
        offset_y = self._widget.center[1]-self._widget.norm_image_size[1]/2

        scale_ratio = self._widget.texture_size[0]/self._widget.norm_image_size[0]
        
        texture_x = (touch.x - offset_x)*scale_ratio
        texture_y = (touch.y - offset_y)*scale_ratio
         
        self._label.text = 'X: {x}, Y: {y}'.format(
            x=texture_x,
            y=texture_y
        )
        self._label.texture_update()
        self._label.pos = touch.pos
        self._label.size = self._label.texture_size[0] + 20, self._label.texture_size[1] + 20

        
class CropAction(object):
    def __init__(self, widget, touch):
        
        self._widget = widget
        
        self._group = str(touch.uid)

        self._start_pos = touch.pos
        with self._widget.canvas:
            Color(1, 1, 1, .3, mode='rgba', group=self._group)
            self._rect = \
                Rectangle(pos=self._start_pos, size=(1, 1), group=self._group)
        
    def on_touch_move(self, touch):
        
        self._rect.size = [c-s for c, s in zip(touch.pos, self._start_pos)]

    def on_touch_up(self, touch):
        
        self._widget.canvas.remove_group(self._group)
        
        coords = (
            min(self._start_pos[0], touch.pos[0]),
            min(self._start_pos[1], touch.pos[1]),
            max(self._start_pos[0], touch.pos[0]),
            max(self._start_pos[1], touch.pos[1]),
        )
        self._widget.roiSelect(coords)


class TouchAsyncImage(AsyncImage):
    
    def __init__(self, *args, **kwargs):
        super(TouchAsyncImage, self).__init__(*args, **kwargs)
        self._keyboard = Window.request_keyboard(self._keyboard_closed, self)
        self._keyboard.bind(on_key_down=self._on_keyboard_down)
        self._keyboard.bind(on_key_up=self._on_keyboard_up)
        self._ctrl_held = False
        
    def _keyboard_closed(self):
        self._keyboard.unbind(on_key_down=self._on_keyboard_down)
        self._keyboard = None

    def _on_keyboard_down(self, keyboard, keycode, text, modifiers):
        if keycode[1] == 'ctrl':
            self._ctrl_held = True

        return True
    
    def _on_keyboard_up(self, *args, **kwargs):
        self._ctrl_held = False

        return True

    def on_touch_down(self, touch):
        
        #
        # Check if mouse event
        #
        if touch.device == 'mouse' and touch.button in ('scrolldown', 'scrollup'):
            
            #
            # Check if the scroll wheel is used
            #
            if touch.button == 'scrolldown' and self.parent.scale > 0.6:
                self.parent.scale -= 0.1
            elif touch.button == 'scrollup':
                self.parent.scale += 0.1
            
            return super(TouchAsyncImage, self).on_touch_down(touch)
        
        touch.grab(self)
        
        if self._ctrl_held:
            touch.ud['action'] = CropAction(self, touch)
            return True
        
        else:
            touch.ud['action'] = CoordsAction(self, touch)
        
        return super(TouchAsyncImage, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        
        if touch.grab_current is not self:
            return super(TouchAsyncImage, self).on_touch_move(touch)

        touch.ud['action'].on_touch_move(touch)
         
        return super(TouchAsyncImage, self).on_touch_move(touch)
        
    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(TouchAsyncImage, self).on_touch_up(touch)
        
        touch.ud['action'].on_touch_up(touch)
        touch.ud['action'] = None
        
        touch.ungrab(self)
        
        return super(TouchAsyncImage, self).on_touch_up(touch)

    def roiSelect(self, coords):
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

        def callback_factory(img_path):
            def callback(instance):
                self.root.images_gallery.scatter_image.source = img_path
    
            return callback
        
        for img_path, img_tn_path, data_path in images_list:
            btn = Button(
                size_hint=(None, None),
                size=(100, 75),
                background_normal=img_tn_path,
                border=(0,0,0,0)
            )
    
            btn.bind(on_press=callback_factory(img_path))
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
        config.setdefaults(
            'CV', {'image_rescaling': 0.25}
        )
    
        #
        # Disable multi touch emulation with the mouse.
        #
        from kivy.config import Config
        Config.set('input', 'mouse', 'mouse,disable_multitouch')
        
    def build_settings(self, settings):
        """Build the settings menu."""
        
        settings.add_json_panel("Network", self.config, data=network_json)
        settings.add_json_panel("Camera", self.config, data=camera_json)
        settings.add_json_panel("CV", self.config, data=cv_json)
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
        elif section == 'CV':
            args = {
                'image_rescaling': self.config.get('CV', 'image_rescaling'),
            }
            server.access('cv', args=args)
            
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
