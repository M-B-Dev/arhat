import kivy
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
import requests 
from requests.auth import HTTPBasicAuth
import json
from kivy.uix.widget import Widget
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder



class MainWindow(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    data = StringProperty('')

    def pressed(self):
        if self.username.text and self.password.text:
            response = requests.post('http://localhost:5000/api/tokens', auth=HTTPBasicAuth(self.username.text, self.password.text))
            if 'token' in json.loads(response.content):
                token = json.loads(response.content)['token']
                ident = json.loads(response.content)['id']
                hed = {'Authorization': 'Bearer ' + token}
                response = requests.get(f'http://localhost:5000/api/users/{ident}', headers=hed)
                self.data = str(json.loads(response.content))
                self.manager.current = "second"
            else:
                return None
            self.username.text = ''
            self.password.text = ''
            return token
        else:
            return None

class SecondWindow(Screen):
    label_text = StringProperty('')


class WindowManager(ScreenManager):
    pass

kv = Builder.load_file("arhat.kv")

class Arhat(App):

    def build(self):
        return kv

if __name__ == "__main__":
    Arhat().run()