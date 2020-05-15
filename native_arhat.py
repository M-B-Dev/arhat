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
from datetime import datetime



class MainWindow(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    data = StringProperty('')
    tasks = StringProperty('')
    token = StringProperty('')
    ident = ObjectProperty(None)

    def pressed(self):
        if self.username.text and self.password.text:
            response = requests.post('http://localhost:5000/api/tokens', auth=HTTPBasicAuth(self.username.text, self.password.text))
            if 'token' in json.loads(response.content):
                token = json.loads(response.content)['token']
                self.token = token
                ident = json.loads(response.content)['id']
                self.ident = ident
                date = datetime.strftime(datetime.today(), "%d-%m-%Y")
                hed = {'Authorization': 'Bearer ' + token}
                response = requests.get(f'http://localhost:5000/api/users/{ident}', headers=hed)
                user_tasks = requests.get(f'http://localhost:5000/api/users/tasks/{ident}/{date}', headers=hed)
                self.data = json.loads(response.content)['username']
                self.tasks = str(json.loads(user_tasks.content)['items'][0]['body'])
                self.manager.current = "second"
            else:
                return None
            self.username.text = ''
            self.password.text = ''
            return token
        else:
            return None

class SecondWindow(Screen):
    token = StringProperty('')
    label_text = StringProperty('')
    task_text = StringProperty('')
    start_time = ObjectProperty(None)
    end_time = ObjectProperty(None)
    task_description = ObjectProperty(None)
    ident = ObjectProperty(None)

    def pressed(self):
        print(self.token)
        hed = {'Authorization': 'Bearer ' + self.token}
        date = datetime.strftime(datetime.today(), "%d-%m-%Y")
        data = {
            "body": self.task_description.text,
            "start_time": self.start_time.text,
            "end_time": self.end_time.text
        }
        response = requests.post(f'http://localhost:5000/api/users/tasks/{self.ident}/{date}', json=data, headers=hed)
        self.start_time.text = ''
        self.end_time.text = ''
        self.task_description.text = ''


class WindowManager(ScreenManager):
    pass

kv = Builder.load_file("arhat.kv")

class Arhat(App):

    def build(self):
        return kv

if __name__ == "__main__":
    Arhat().run()