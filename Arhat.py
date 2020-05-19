from kivy.lang import Builder
from kivy.factory import Factory
from kivymd.app import MDApp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty, StringProperty
import requests 
from requests.auth import HTTPBasicAuth
import json
from kivymd.theming import ThemableBehavior
from kivymd.uix.list import OneLineIconListItem, MDList
from kivymd.uix.picker import MDDatePicker, MDTimePicker
from datetime import datetime
from kivymd.uix.label import MDLabel

class ContentNavigationDrawer(BoxLayout):
    window_manager = ObjectProperty()
    nav_drawer = ObjectProperty()

class Login(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    token = ObjectProperty(None)
    user_id = ObjectProperty(None)


    def login_user(self):
        if self.username.text and self.password.text:
            response = requests.post('http://localhost:5000/api/tokens', auth=HTTPBasicAuth(self.username.text, self.password.text))
            if 'token' in json.loads(response.content):
                self.token = json.loads(response.content)['token']
                self.user_id = json.loads(response.content)['id']
                self.manager.current = "Tasks"
            else:
                return None
            self.username.text = ''
            self.password.text = ''
            return self.token


class Register(Screen):
    Rusername = ObjectProperty(None)
    email = ObjectProperty(None)
    password1 = ObjectProperty(None)
    password12 = ObjectProperty(None)

class MyLabel(MDLabel):
    pass

class Tasks(Screen):
    tasks = ObjectProperty(None)
    token = ObjectProperty(None)
    user_id = ObjectProperty(None)

    def load_tasks(self, date):
        if not date:
            date = datetime.strftime(datetime.today(), "%d-%m-%Y")
        hed = {'Authorization': 'Bearer ' + self.token}
        user_tasks = requests.get(f'http://localhost:5000/api/users/tasks/{self.user_id}/{date}', headers=hed)
        self.tasks = json.loads(user_tasks.content)['items']
        for task in self.tasks:
            self.add_widget(MyLabel(text=task['body'], halign="center", valign="top"))

    

class NewTask(Screen):
    token = ObjectProperty(None)
    user_id = ObjectProperty(None)
    task_description = ObjectProperty(None)
    start_time = ObjectProperty(None)
    end_time = ObjectProperty(None)
    frequency = ObjectProperty(None)
    start_date = ObjectProperty(None)
    end_date = ObjectProperty(None)
    start_time_minutes = ObjectProperty(None)
    end_time_minutes = ObjectProperty(None)
    updated_tasks = ObjectProperty(None)
    

    def get_end_date(self, date):
        '''
        :type date: <class 'datetime.date'>
        '''
        self.end_date.text = datetime.strftime(date, "%d-%m-%Y")

    def get_start_date(self, date):
        '''
        :type date: <class 'datetime.date'>
        '''
        self.start_date.text = datetime.strftime(date, "%d-%m-%Y")

    def show_date_picker(self, mode):
        if mode == "end":
            date_dialog = MDDatePicker(callback=self.get_end_date)
        else:
            date_dialog = MDDatePicker(callback=self.get_start_date)
        date_dialog.open()

    def show_start_time_picker(self):
        time_dialog = MDTimePicker()
        time_dialog.bind(time=self.get_start_time)
        time_dialog.open()

    def get_start_time(self, instance, time):
        self.start_time.text = str(time)
        self.start_time_minutes = time

    def show_end_time_picker(self):
        time_dialog = MDTimePicker()
        time_dialog.bind(time=self.get_end_time)
        time_dialog.open()

    def get_end_time(self, instance, time):
        self.end_time.text = str(time)
        self.end_time_minutes = time


    def create_new_task(self):
        if self.end_time_minutes and self.start_time_minutes and self.start_date:
            self.end_time_minutes = (self.end_time_minutes.hour * 60) + self.end_time_minutes.minute
            self.start_time_minutes = (self.start_time_minutes.hour * 60) + self.start_time_minutes.minute
            if self.frequency.text:
                frequency = int(self.frequency.text)
            else:
                frequency = None
            if self.end_date.text:
                to_date = self.end_date.text
            else:
                to_date = None
            data = {
                'body': self.task_description.text, 
                'start_time': self.start_time_minutes, 
                'end_time': self.end_time_minutes, 
                'frequency': frequency, 
                'date': self.start_date.text, 
                'to_date': to_date,
                'user_id': self.user_id
            }
            hed = {'Authorization': 'Bearer ' + self.token}
            response = requests.post(f'http://localhost:5000/api/users/tasks/{self.user_id}/{self.start_date.text}', json=data, headers=hed)
            self.task_description = ObjectProperty(None)
            self.start_time = ObjectProperty(None)
            self.end_time = ObjectProperty(None)
            self.frequency = ObjectProperty(None)
            self.start_date = ObjectProperty(None)
            self.end_date = ObjectProperty(None)
            self.start_time_minutes = ObjectProperty(None)
            self.end_time_minutes = ObjectProperty(None)
            self.updated_tasks = json.loads(response.content)
            self.manager.current = "Tasks"
        
class LoginButton(OneLineIconListItem):
    hide = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.hide:
            self.text = "Login"
            self.icon = "account-circle"


class RegisterButton(OneLineIconListItem):
    hide = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Register"
        self.icon = "account-plus"

class EditProfileButton(OneLineIconListItem):
    hide = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Edit Profile"
        self.icon = "account-circle-outline"

class ContactsButton(OneLineIconListItem):
    hide = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Contacts"
        self.icon = "account-multiple"

class TasksButton(OneLineIconListItem):
    hide = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Tasks"
        self.icon = "calendar-multiple-check"

class NewTaskButton(OneLineIconListItem):
    hide = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "New Task"
        self.icon = "calendar-check"

class MessagesButton(OneLineIconListItem):
    hide = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Messages"
        self.icon = "message-text-outline"

class LogoutButton(OneLineIconListItem):
    hide = ObjectProperty(None)
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text = "Logout"
        self.icon = "logout"


class MainApp(MDApp):
    def __init__(self, **kwargs):
        self.title = "Arhat"
        self.theme_cls.primary_palette = "BlueGray"
        super().__init__(**kwargs)

    def build(self):
        return Builder.load_file("arhat.kv")

if __name__ == "__main__":
    MainApp().run()