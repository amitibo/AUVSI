__author__ = 'Ori'
from kivy.properties import ListProperty, ObjectProperty
from kivy.uix.scatter import Scatter
from kivy.uix.widget import Widget

from kivy.properties import StringProperty

from AUVSIcv.images import Image

from kivy.support import install_twisted_reactor
install_twisted_reactor()
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.stencilview import StencilView
from kivy.graphics import Color, Rectangle, Point, GraphicException
from kivy.uix.image import AsyncImage

import os
from bisect import bisect
from AUVSIground.utils import decimal_to_minsec, FileSelector


DB_MAIN_FOLDER = r"C:\Users\Ori\Desktop\Database_Auvsi\decent"
DATA_FOLDER = os.path.join(DB_MAIN_FOLDER, r"images_data")
RESIZE_FOLDER = os.path.join(DB_MAIN_FOLDER, r"resized")
def data_path(timestamp):
    data_list = sorted(os.listdir(DATA_FOLDER))
    data_index = bisect(data_list, timestamp)
    r_index = max(data_index-1, 0)
    data_name = data_list[r_index]

    return os.path.join(DATA_FOLDER, data_name)


class CoordsAction(object):
    """
    Returns the coordinates of the point where it was clicked and called
    Draw a "cross-air" and updates a text-box with the coordinates values
    """
    def __init__(self, widget, touch, coords_text, image):

        self._coords_text = coords_text
        self._widget = widget
        self._image = image
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

        lat, lon = self._image.coords2LatLon(texture_x, texture_y)
        lat_lon_formater = 'Lat: {}, Lon: {}'.format
        self._label.text = lat_lon_formater(lat, lon)

        self._label.texture_update()
        self._label.pos = touch.pos
        self._label.size = self._label.texture_size[0] + 20, self._label.texture_size[1] + 20

        minsec_lat, minsec_lon = decimal_to_minsec(lat, lon)
        self._coords_text.text = lat_lon_formater(minsec_lat, minsec_lon)


class ExaminationWidget(Widget):
    images_folder = StringProperty(RESIZE_FOLDER)

    def __init__(self, **kwargs):
        """
        should get parameter images_folder
        """
        super(self.__class__, self).__init__(**kwargs)
        self.file_selector = FileSelector(self.images_folder, "jpg")
        # first_image = os.path.join(self.file_selector.dir_path,
        #                            self.file_selector.current_file)
        # self.ids.image_viewer.source = first_image

    def _update_image_name(self):
        print "Image was updated"

    def _reset_image_view(self):
        self.ids["scatter"].scale = 1
        self.ids["scatter"].center = self.ids["scatter"].parent.center

    def next_image(self):
        try:
            next_image_name = self.file_selector.next_file()
            self._reset_image_view()
            self.ids["image_data"].text = next_image_name
        except NoFiles:
            return

        next_image = os.path.join(self.file_selector.dir_path, next_image_name)
        self.ids.image_viewer.source = next_image
        self._update_image_name()


    def previous_image(self):
        try:
            prev_image_name = self.file_selector.prev_file()
            self._reset_image_view()
            self.ids["image_data"].text = prev_image_name
        except NoFiles:
            return

        next_image = os.path.join(self.file_selector.dir_path, prev_image_name)
        self.ids.image_viewer.source = next_image
        self._update_image_name()


class TouchAsyncImage(AsyncImage):

    def on_touch_down(self, touch):

        #
        # Check if mouse event
        #
        if touch.device == 'mouse' and touch.button in ('scrolldown', 'scrollup'):

            #
            # Check if the scroll wheel is used
            #
            if touch.button == 'scrolldown' and self.parent.scale > 0.6:
                self.parent.scale += 0.1
            elif touch.button == 'scrollup':
                self.parent.scale -= 0.1

            return super(TouchAsyncImage, self).on_touch_down(touch)

        touch.grab(self)
        try:
            timestamp = os.path.basename(self.source).split('.')[0]
            im_data_path = data_path(timestamp)
            image_and_data = Image(self.source, im_data_path)
            touch.ud['action'] = CoordsAction(self, touch, self.coords_display,
                                              image_and_data)
        except TypeError:
            print "No file was loaded"
        except KeyError:
            print "Data file doesn't contain K matrix"
            touch.ud['action'] = None

        return super(TouchAsyncImage, self).on_touch_down(touch)

    def on_touch_move(self, touch):

        if touch.grab_current is not self:
            return super(TouchAsyncImage, self).on_touch_move(touch)

        try:
            touch.ud['action'].on_touch_move(touch)
        except KeyError:
            print "No file was loaded, so touch.ud['action'] wasn't assigned"
        except AttributeError:
            print "touch.ud['action'] was defined as None, because coords weren't available," \
                  " thus doesn't have on_touch_move attribute"



        return super(TouchAsyncImage, self).on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is not self:
            return super(TouchAsyncImage, self).on_touch_up(touch)

        try:
            touch.ud['action'].on_touch_up(touch)
            touch.ud['action'] = None
        except AttributeError:
            print "Coordinates are not available, thus touch.ud['action'] is None"
        except KeyError:
            print "No file was loaded, so touch.ud['action'] wasn't assigned"

        touch.ungrab(self)

        return super(TouchAsyncImage, self).on_touch_up(touch)


class NoFiles(Exception):
    pass


class BoxStencil(BoxLayout, StencilView):
    pass


class ScatterStencil(Scatter):
    """
    a class written by amit.
    allows to use scatter with the character of 'cropping'
    the touch down if touched isn't in the wanted place
    """
    def on_touch_down(self, touch):

        stencil = self.stencil

        #
        # Check if inside the encapsulating stencil.
        #
        if not stencil.collide_point(*self.to_window(*touch.pos)):
            return False

        return super(ScatterStencil, self).on_touch_down(touch)