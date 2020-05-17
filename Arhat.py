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

class ContentNavigationDrawer(BoxLayout):
    window_manager = ObjectProperty()
    nav_drawer = ObjectProperty()

class Login(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    token = ObjectProperty(None)
    hide = ObjectProperty(None)

    def login_user(self):
        if self.username.text and self.password.text:
            response = requests.post('http://localhost:5000/api/tokens', auth=HTTPBasicAuth(self.username.text, self.password.text))
            if 'token' in json.loads(response.content):
                self.token = json.loads(response.content)['token']
                print(self.token)
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

class Tasks(Screen):
    pass

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