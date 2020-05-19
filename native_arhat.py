import kivy
from kivymd.app import MDApp
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
from kivymd.uix.picker import MDDatePicker, MDTimePicker


class Login(Screen):
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
                # self.tasks = str(json.loads(user_tasks.content)['items'][0]['body'])
                self.manager.current = "tasks"
            else:
                return None
            self.username.text = ''
            self.password.text = ''
            return token
        else:
            return None

class NewTask(Screen):
    token = StringProperty('')
    label_text = StringProperty('')
    task_text = StringProperty('')
    start_time = ObjectProperty(None)
    end_time = ObjectProperty(None)
    task_description = ObjectProperty(None)
    ident = ObjectProperty(None)
    end_date = ObjectProperty(None)
    frequency = ObjectProperty(None)

    def pressed(self):
        print(self.start_time.text)
        print(self.end_time.text)
        print(self.end_date.text)
        print(self.frequency.text)
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


    def get_date(self, date):
        '''
        :type date: <class 'datetime.date'>
        '''


    def show_date_picker(self):
        date_dialog = MDDatePicker(callback=self.get_date)
        date_dialog.open()

    def show_time_picker(self):
        '''Open time picker dialog.'''

        time_dialog = MDTimePicker()
        time_dialog.bind(time=self.get_time_picker_date)
        time_dialog.open()
    


class EditTask(Screen):
    pass

class NewTask(Screen):
    pass

class Tasks(Screen):
    pass

class EditProfile(Screen):
    pass

class WindowManager(ScreenManager):
    pass



class Arhat(MDApp):

    def build(self):
        kv = Builder.load_file("arhat.kv")
        return kv

if __name__ == "__main__":
    Arhat().run()