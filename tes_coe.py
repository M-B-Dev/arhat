from kivy.app import App  
from kivy.uix.behaviors import ButtonBehavior  
from kivy.uix.image import Image  


class ImageButton(ButtonBehavior, Image):
    pass


class MyApp(App):  
    def build(self):  
        return ImageButton(size=[200, 100], color=(0.5,0.5,1,1), pos=(500, 500), source="kivy.png", on_press=lambda *args: print("press"))

if __name__ == "__main__":  
    MyApp().run()  