__author__ = 'Ori'
from kivy.app import App
from screens import MyScreenManager



class GuiApp(App):
    def build(self):
        return MyScreenManager()

if __name__ == "__main__":
    GuiApp().run()

