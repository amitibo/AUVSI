import kivy
kivy.require('1.0.6')  # replace with your current kivy version !

from kivy.app import App
from kivy.uix.button import Button
from kivy.uix.stacklayout import StackLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatter import Scatter
from kivy.uix.tabbedpanel import TabbedPanel
from kivy.properties import ObjectProperty

import glob


class ImagesGalleryWin(BoxLayout):
    scatter_image = ObjectProperty()
    stacked_layout = ObjectProperty()

    #layout = StackLayout(spacing=10, size_hint_y=None)
    #layout.bind(minimum_height=layout.setter('height'))        

class ImageGalleryApp(App):
    def build(self):
        root = self.root
        
        img_list = glob.glob('../data/*.jpg')

        def callback(instance):
            root.scatter_image.source = instance.background_normal

        for i in range(100):
            btn = Button(
                size_hint=(None, None),
                size=(100, 100),
                background_normal=img_list[i%len(img_list)],
                border=(0,0,0,0)
            )
            
            btn.bind(on_press=callback)
            self.root.stacked_layout.add_widget(btn)        
        
        return root
    
    #def build(self):
        #
        
        #right_btn = Button(size_hint_x=1, border=(0, 0, 0, 0))
        

        #sv = ScrollView(size_hint_x=1)
        #sv.add_widget(layout)
        
        #root = BoxLayout()
        #root.add_widget(sv)
        #root.add_widget(right_btn)

        #return root
    
    
if __name__ == '__main__':
    ImageGalleryApp().run()


