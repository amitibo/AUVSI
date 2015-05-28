__author__ = 'Ori'
from kivy.app import App
from screens import MyScreenManager
from kivy.uix.settings import SettingsWithTabbedPanel
from settingsjson import *
from payload_control import Payload, PayloadDebug


class GuiApp(App):
    def __init__(self, **kwargs):
        super(GuiApp, self).__init__(**kwargs)
        self.payload_controller = Payload('192.168.1.101')
        self.payload_debug = PayloadDebug

    def build(self):
        self.settings_cls = SettingsWithTabbedPanel
        # We don't want the common user to change the kivy settings
        self.use_kivy_settings = False
        return MyScreenManager()

    def build_config(self, config):
        """Create the default config (used the first time the application is run)"""

        config.setdefaults(
            'Network', {'IP': '192.168.1.101', 'port': 8855}
            )
        camera_def_settings = {'ISO': 100, 'Shutter': 5000, 'Aperture': 4, 'Zoom': 45}
        config.setdefaults(
            'Camera', camera_def_settings
            )
        config.setdefaults(
            "GS' Database", {'path': r"C:\Users\Ori\Desktop\Yossi_Elbaz"}
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

    def on_config_change(self, config, section, key, value):
        """
        Handle change in the settings
        """

        if section == 'Network':
            self.connect_to_server()
        elif section == 'Camera':
            args = {
                'ISO': self.config.get('Camera', 'iso'),
                'shutter': self.config.get('Camera', 'shutter'),
                'aperture': self.config.get('Camera', 'aperture'),
                'zoom': self.config.get('Camera', 'zoom'),
            }
            #
            # server.access('camera_set', args=args) - This is where you suppose to change the settings
            #

    def connect_to_server(self):
        """
        Initiate connection to airborne server
        """
        pass

    def on_connection(self, connection):
        """
        Callback on successful connection to the server
        """
        pass

    def on_disconnection(self, connection):
        """
        Callback on disconnection from the server
        """
        pass

if __name__ == "__main__":
    GuiApp().run()

