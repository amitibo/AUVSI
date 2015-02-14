#install_twisted_rector must be called before importing the reactor
from kivy.support import install_twisted_reactor
install_twisted_reactor()

from twisted.internet import reactor
import server

from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty
import pkg_resources
import os


class BGLabel(Label):
    pass


class ImageProcessingGui(BoxLayout):
    connect_state = ObjectProperty()
    
    def shoot(self, state):
        server.access('camera=on')
        
        
# A simple kivy App, with a textbox to enter messages, and
# a large label to display all the messages received from
# the server
class GUIApp(App):
    kv_directory = pkg_resources.resource_filename(__package__, 'resources')
    connection = None

    def build(self):
        self.connect_to_server()

    def connect_to_server(self):
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
        
if __name__ == '__main__':
    GUIApp().run()
