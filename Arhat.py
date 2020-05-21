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
from kivy.graphics import Rectangle, Color
from webcolors import hex_to_rgb
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.behaviors import ButtonBehavior  
from kivy.uix.image import Image  
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton, MDRoundFlatButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox

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

class Scrollable(ScrollView):
    def __init__(self, task, **kwargs):
        super(Scrollable, self).__init__(**kwargs)
        self.widg = Content(task=task)
        self.add_widget(self.widg)
        self.height = 300


class Content(BoxLayout):
    def __init__(self, task, **kwargs):
        super(Content, self).__init__(**kwargs)
        self.done_data = False
        self.body = MDTextField(text=task['body'], size_hint_y=None)
        self.start_time_minutes = self.set_time(task['start_time'])
        self.end_time_minutes = self.set_time(task['end_time'])
        self.start_time = MDRoundFlatButton(text=f"Start Time: {self.start_time_minutes}", size_hint_y=None)
        self.start_time.bind(on_press=self.show_start_time_picker)
        self.end_time = MDRoundFlatButton(text=f"End Time: {self.end_time_minutes}", size_hint_y=None)
        self.end_time.bind(on_press=self.show_end_time_picker)
        self.frequency = MDTextField(text=str(task['frequency']), size_hint_y=None)
        if str(task['to_date']) == "None":
            self.to_date = MDRoundFlatButton()
            self.date_to = None
        else:
            self.to_date = MDRoundFlatButton(text=str(task['to_date']))
            self.date_to = task['to_date']
        self.to_date.bind(on_press=self.show_date_picker)
        self.done = CheckBox()
        self.done.bind(active=self.on_checkbox_active)
        self.add_widget(self.start_time)
        self.add_widget(self.end_time)
        self.add_widget(self.body)
        self.add_widget(self.frequency)
        self.add_widget(self.to_date)
        self.add_widget(self.done)
        self.size_hint_y = None
        self.height = 400

    def get_to_date(self, date):
        '''
        :type date: <class 'datetime.date'>
        '''
        self.date_to = datetime.strftime(date, "%d-%m-%Y")
        self.to_date.text = f"Date to: {self.date_to}"

    def show_date_picker(self, instance):
        date_dialog = MDDatePicker(callback=self.get_to_date)
        date_dialog.open()

    def on_checkbox_active(self, checkbox, value):
        if value:
            self.done_data = True


    def show_start_time_picker(self, instance):
        time_dialog = MDTimePicker()
        time_dialog.bind(time=self.get_start_time)
        time_dialog.open()

    def get_start_time(self, instance, time):
        self.start_time_minutes = time
        self.start_time.text = f"Start Time: {str(self.start_time_minutes)}"

    def show_end_time_picker(self, instance):
        time_dialog = MDTimePicker()
        time_dialog.bind(time=self.get_end_time)
        time_dialog.open()

    def get_end_time(self, instance, time):
        self.end_time_minutes = time
        self.end_time.text = f"End Time: {str(self.end_time_minutes)}"

    def set_time(self, time):
        if time > 599:
            hour = str(time/60)[0:2]
        else:
            hour = f"0{str(time/60)[0:1]}"
        minutes = time - (int(hour)*60)
        if minutes > 9:
            return f"{hour}:{minutes}"
        else:
            return f"{hour}:0{minutes}"

class ImageButton(ButtonBehavior, Image):
    def __init__(self, task, inst, **kwargs):
        super(ImageButton, self).__init__(**kwargs)
        self.text='test'
        self.size_hint_y = None
        self.size_hint_x = None
        self.task = task
        self.inst = inst
        self.on_press = lambda *args: self.show_edit_task()
        with self.canvas.before:
            self.lbl_staticText = Label(font_size=12, color=(0,0,0,1)) 
            self.lbl_staticText.text = f"{task['body']}: Start time: {self.set_time(task['start_time'])} Finish time: {self.set_time(task['end_time'])}"
            self.lbl_staticText.texture_update()
            self.lbl_staticText.pos = self.pos
            self.lbl_staticText.size = self.size

    def show_edit_task(self):
        task_screen = Tasks(token=self.inst.token, user_id=self.inst.user_id)
        self.edit_task = MDDialog(
                auto_dismiss=False,
                title="Edit task:",
                type="custom",
                content_cls=Scrollable(task=self.task),
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_press=self.close_dialog
                    ),
                    MDFlatButton(
                        text="OK",
                        on_press=self.update_task
                    ),
                ],
            )
        self.edit_task.create_items()
        self.edit_task.open()

    def close_dialog(self, q):
        self.edit_task.dismiss()

    def update_task(self, q):
        if self.edit_task:
            print(self.task['id'])
            body = self.edit_task.content_cls.widg.body.text
            start_minutes = (int(str(self.edit_task.content_cls.widg.start_time_minutes)[0:2])*60) + int(str(self.edit_task.content_cls.widg.start_time_minutes)[-2])
            end_minutes = (int(str(self.edit_task.content_cls.widg.end_time_minutes)[0:2])*60) + int(str(self.edit_task.content_cls.widg.end_time_minutes)[-2])
            frequency = int(self.edit_task.content_cls.widg.frequency.text)
            date_to = self.edit_task.content_cls.widg.date_to
            done = self.edit_task.content_cls.widg.done_data
            print(done)
            data = {
                'body': body, 
                'done': done, 
                'start_time': start_minutes, 
                'end_time': end_minutes, 
                'frequency': frequency, 
                'to_date': date_to
            }
            hed = {'Authorization': 'Bearer ' + self.inst.token}
            response = requests.put(f'http://localhost:5000/api/users/tasks/{self.task["id"]}', json=data, headers=hed)
            self.edit_task.dismiss()


    def set_time(self, time):
        if time > 599:
            hour = str(time/60)[0:2]
        else:
            hour = f"0{str(time/60)[0:1]}"
        minutes = time - (int(hour)*60)
        if minutes > 9:
            return f"{hour}:{minutes}"
        else:
            return f"{hour}:0{minutes}"

class Tasks(Screen):
    tasks = ObjectProperty(None)
    token = ObjectProperty(None)
    user_id = ObjectProperty(None)

    def load_tasks(self, date=datetime.strftime(datetime.today(), "%d-%m-%Y")):
        hed = {'Authorization': 'Bearer ' + self.token}
        user_tasks = requests.get(f'http://localhost:5000/api/users/tasks/{self.user_id}/{date}', headers=hed)
        self.tasks = json.loads(user_tasks.content)['items']

        for task in self.tasks:
            color = hex_to_rgb("#" + task['color'])
            self.button = ImageButton(
                inst=self,
                task=task, 
                pos=(
                    (self.parent.width/2)-250, 
                    self.parent.height - (int(task['end_time']))/3
                    ), 
                size=(500,(int(task['end_time'])-int(task['start_time']))/3), 
                color=(color[0]/255, color[1]/255, color[2]/255, .5), 
                source=None
                )
            self.add_widget(self.button)

    
    def show_edit_task(self, task):
        print(task['id'])

    def set_time(self, time):
        if time > 599:
            hour = str(time/60)[0:2]
        else:
            hour = f"0{str(time/60)[0:1]}"
        minutes = time - (int(hour)*60)
        if minutes > 9:
            return f"{hour}:{minutes}"
        else:
            return f"{hour}:0{minutes}"

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