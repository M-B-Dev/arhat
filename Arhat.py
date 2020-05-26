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
from kivymd.uix.list import OneLineIconListItem, MDList, IconLeftWidget
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
from kivymd.uix.button import MDFlatButton, MDRoundFlatButton, MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivy.uix.scrollview import ScrollView
from kivy.uix.checkbox import CheckBox
from kivy.uix.colorpicker import ColorPicker
from kivymd.uix.picker import MDThemePicker
import matplotlib
from colour import Color
from kivymd.color_definitions import colors
from validate_email import validate_email

class ScreenManagement(ScreenManager):
    pass

class ContentNavigationDrawer(BoxLayout):
    window_manager = ObjectProperty()
    nav_drawer = ObjectProperty()

class Login(Screen):
    username = ObjectProperty(None)
    password = ObjectProperty(None)
    token = ObjectProperty(None)
    user_id = ObjectProperty(None)
    user = ObjectProperty(None)
    internal_password = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(Login, self).__init__(**kwargs)
        self.token = ''

    def login_user(self):
        if self.username.text and self.password.text:
            response = requests.post('http://localhost:5000/api/tokens', auth=HTTPBasicAuth(self.username.text, self.password.text))
            if 'token' in json.loads(response.content):
                self.token = json.loads(response.content)['token']
                self.user_id = json.loads(response.content)['id']
                self.manager.current = "Tasks"
            else:
                return None
            self.internal_password = self.password.text
            self.username.text = ''
            self.password.text = ''
            hed = {'Authorization': 'Bearer ' + self.token}
            self.user = json.loads(requests.get(f'http://localhost:5000/api/users/{self.user_id}', headers=hed).content)
            return self.token


class Register(Screen):
    rusername = ObjectProperty(None)
    email = ObjectProperty(None)
    password1 = ObjectProperty(None)
    password2 = ObjectProperty(None)

    def register_new_user(self):
        errors = {}
        if not self.email.text or validate_email(self.email.text) is not True:
            errors['email'] = "Please enter a valid email address."
        if not self.password1.text and not self.password2.text or self.password1.text != self.password2.text:
            errors['password'] = "Please enter matching passwords."
        if errors:
            for error in errors.keys():
                if error == 'email':
                    self.email.helper_text_mode = "persistent"
                    self.email.helper_text = errors['email']
                    self.email.error = True
                if error == 'password':
                    self.password1.helper_text_mode = "persistent"
                    self.password2.helper_text_mode = "persistent"
                    self.password1.error = True
                    self.password2.error = True
                    self.password1.helper_text = errors['password']
                    self.password2.helper_text = errors['password']
            return False
        data = {
            'username': self.rusername.text,
            'email': self.email.text,
            'password': self.password1.text
        }
        response = requests.post('http://localhost:5000/api/users', json=data)
        if 'error' in json.loads(response.content):
            if 'username' in json.loads(response.content)['message']:
                self.rusername.helper_text_mode = "persistent"
                self.rusername.helper_text = json.loads(response.content)['message']
                self.rusername.error = True
            if 'email' in json.loads(response.content)['message']:
                self.email.helper_text_mode = "persistent"
                self.email.error = True
                self.email.helper_text = json.loads(response.content)['email']
            return False
        return True



class EditProfile(Screen):
    user = ObjectProperty(None)
    internal_password = ObjectProperty(None)
    token = ObjectProperty(None)

    def set_text_fields(self):
        number_of_widgets = len(self.children[0].children[1].children)
        for i in range(number_of_widgets):
            self.children[0].children[1].remove_widget(self.children[0].children[1].children[0])
        self.field_names = {
            'username': self.user['username'],
            'email': self.user['email'],
            'password1': self.internal_password,
            'password2': self.internal_password,
            'days': str(self.user['days']),
            'threshold': str(self.user['threshold']) 
        }
        y = 0.9
        for field in self.field_names.keys():
            if 'password' in field:
                password = True
            else:
                password = False
            setattr(self, field, MDTextField(
                id=field,
                text=self.field_names[field],
                required=True,
                mode="rectangle",
                pos_hint={"center_x": 0.5, "center_y": y},
                password=password
            ))
            y - 0.2
            widget = getattr(self, field)
            self.children[0].children[1].add_widget(widget)
        self.edit_profile_button = MDRaisedButton(text="Edit Profile", pos_hint={"center_x": 0.5, "center_y": 0})
        self.edit_profile_button.bind(on_release=self.edit_profile)
        self.children[0].children[1].add_widget(self.edit_profile_button)
        
            

    def edit_profile(self, instance):
        errors = False
        if self.password1.text != self.password2.text or len(self.password1.text) < 8:
            self.password1.helper_text = "Please enter identical passwords of 8 characters or more."
            self.password2.helper_text = "Please enter identical passwords of 8 characters or more."
            self.password1.helper_text_mode = "persistent"
            self.password2.helper_text_mode = "persistent"
            errors = True
        if not self.email.text or validate_email(self.email.text) is False:
            self.email.helper_text = "Please enter a valid email address"
            self.email.helper_text_mode = "persistent"
            errors = True
        if not self.threshold.text or self.threshold.text.isnumeric() is False or int(self.threshold.text) > 100:
            self.threshold.helper_text = "Please enter a number between 0 and 100"
            self.threshold.helper_text_mode = "persistent"
            errors = True
        if not self.days.text or self.days.text.isnumeric() is False:
            self.days.helper_text = "Please enter a number"
            self.days.helper_text_mode = "persistent"
            errors = True
        if errors is True:
            return False
        hed = {'Authorization': 'Bearer ' + self.token}
        data = {
            'username': self.username.text,
            'email': self.email.text,
            'threshold': int(self.threshold.text),
            'days': int(self.days.text),
            'password': self.password1.text
            }
        response = requests.put(f'http://localhost:5000/api/users/{self.user["id"]}', json=data, headers=hed)
        if 'error' in json.loads(response.content):
            if 'username' in json.loads(response.content)['error']:
                self.username.helper_text = "That username is taken" 
                self.username.helper_text_mode = "persistent"
            if 'email' in json.loads(response.content)['error']:
                self.email.helper_text = "That email is already registered" 
                self.email.helper_text_mode = "persistent"
            return False
        self.update_fields()

    def update_fields(self):
        hed = {'Authorization': 'Bearer ' + self.token}
        self.user = json.loads(requests.get(f'http://localhost:5000/api/users/{self.user["id"]}', headers=hed).content)
        self.set_text_fields()


class Messages(Screen):
    def show_received_messages():
        pass
    
    def show_sent_messages():
        pass

    def send_message():
        pass

class Contacts(Screen):
    def show_users():
        #Must display user avatar
        pass

    def show_followers():
        pass

    def show_following():
        pass

    def follow():
        pass

    def unfollow():
        pass

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
        self.id = str(task['id'])
        self.selected_color = None
        self.done_data = False
        self.body = MDTextField(text=task['body'], size_hint_y=None)
        self.start_time_minutes = self.set_time(task['start_time'])
        self.end_time_minutes = self.set_time(task['end_time'])
        self.start_time = Button(text=f"Start Time: {self.start_time_minutes}")
        self.start_time.bind(on_press=self.show_start_time_picker)
        self.end_time = Button(text=f"End Time: {self.end_time_minutes}")
        self.end_time.bind(on_press=self.show_end_time_picker)
        self.color = hex_to_rgb("#" + task['color'])
        self.color_pick = Button(text="Change color", background_color=(self.color[0]/255, self.color[1]/255, self.color[2]/255, .5))
        self.color_pick.bind(on_press=self.show_theme_picker)
        if not task['frequency']:
            frequency = 0
        else:
            frequency = task['frequency']
        self.frequency = MDTextField(text=str(frequency), size_hint_y=None)
        if str(task['to_date']) == "None":
            self.to_date = Button(text="Enter to date")
            self.date_to = None
        else:
            self.to_date = Button(text=f"To date: str(task['to_date'])")
            self.date_to = task['to_date']
        self.to_date.bind(on_press=self.show_date_picker)
        self.done_label = Label(text="Done", color=(0,0,0,1))
        self.done = CheckBox()
        self.done.bind(active=self.on_checkbox_active)
        self.add_widget(self.start_time)
        self.add_widget(self.end_time)
        self.add_widget(self.body)
        self.add_widget(self.frequency)
        self.add_widget(self.to_date)
        self.add_widget(self.done_label)
        self.add_widget(self.done)
        self.add_widget(self.color_pick)
        self.size_hint_y = None
        self.height = 400

    def color_picker(self, color):
        c = hex_to_rgb("#" + colors[color]["900"])
        self.selected_color = colors[color]["900"]
        self.color_pick.background_color = (c[0]/255, c[1]/255, c[2]/255, 0.5)

    def show_theme_picker(self, instance):
        self.theme_dialog = MDThemePicker(id=self.id)
        self.theme_dialog.open()

    def on_color(self, instance, value):
        self.color = str(instance.hex_color)

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

    def close_dialog(self, instance):
        self.edit_task.dismiss()

    def update_task(self, instance):
        if self.edit_task:
            body = self.edit_task.content_cls.widg.body.text
            start_minutes = (int(str(self.edit_task.content_cls.widg.start_time_minutes)[0:2])*60) + int(str(self.edit_task.content_cls.widg.start_time_minutes)[-2])
            end_minutes = (int(str(self.edit_task.content_cls.widg.end_time_minutes)[0:2])*60) + int(str(self.edit_task.content_cls.widg.end_time_minutes)[-2])
            frequency = self.edit_task.content_cls.widg.frequency.text
            date_to = self.edit_task.content_cls.widg.date_to
            done = self.edit_task.content_cls.widg.done_data
            if self.edit_task.content_cls.widg.selected_color:
                color = self.edit_task.content_cls.widg.selected_color
            else:
                color = self.task['color']
            data = {
                'color': color,
                'body': body, 
                'done': done, 
                'start_time': start_minutes, 
                'end_time': end_minutes, 
                'frequency': frequency, 
                'to_date': date_to
            }
            hed = {'Authorization': 'Bearer ' + self.inst.token}
            response = requests.put(f'http://localhost:5000/api/users/tasks/{self.task["id"]}', json=data, headers=hed)
            original_widgets = [child for child in self.parent.children if "ImageButton" in str(type(child))]
            self.parent.load_tasks()
            for child in original_widgets:
                if self.parent:
                    self.parent.remove_widget(child)
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

    
        
    def load_tasks(self, date=datetime.strftime(datetime.today(), "%d-%m-%Y"), height=None, width=None, manager=None):
        self.date = date
        if not width:
            width = self.parent.width
        if not height:
            height = self.parent.height
        if manager:
            self.manager = manager
        hed = {'Authorization': 'Bearer ' + self.token}
        user_tasks = requests.get(f'http://localhost:5000/api/users/tasks/{self.user_id}/{date}', headers=hed)
        self.tasks = json.loads(user_tasks.content)['items']

        for task in self.tasks:
            color = hex_to_rgb("#" + task['color'])
            button = ImageButton(
                inst=self,
                task=task, 
                pos=(
                    (width/2)-250, 
                    height - (int(task['end_time']))/3
                    ), 
                size=(500,(int(task['end_time'])-int(task['start_time']))/3), 
                color=(color[0]/255, color[1]/255, color[2]/255, .5), 
                source=None
                )
            setattr(self, str(task['id']), button)
            self.add_widget(getattr(self, str(task['id'])))
        self.date_button = Button(text=f"Change date: {self.date}", pos=(width/2-250, 0), size_hint_y=None, size_hint_x=None, size=(500, 50))
        self.date_button.bind(on_press=self.show_date_picker)
        self.add_widget(self.date_button)
        self.manager.current = "Tasks"

    def get_date(self, date):
        '''
        :type date: <class 'datetime.date'>
        '''
        self.date = datetime.strftime(date, "%d-%m-%Y")
        
        original_widgets = [child for child in self.children if "ImageButton" in str(type(child))]
        self.load_tasks(date=self.date)
        for child in original_widgets:
            self.remove_widget(child)

    def show_date_picker(self, instance):
        date_dialog = MDDatePicker(callback=self.get_date)
        date_dialog.open()
    
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

class ButtonTemplate(OneLineIconListItem):
    pass

class List(MDList):
    def __init__(self, **kwargs):
        super(List, self).__init__(**kwargs)
        self.nav_buttons = {
            'Tasks': "calendar-multiple-check",
            'New Task': "calendar-check",
            'Messages': "message-text-outline",
            'Contacts': "account-multiple",
            'Edit Profile': "account-circle-outline",
            'Logout': "logout",
            'Login': "account-circle",
            'Register': "account-plus"
        }
        self.logged_out_buttons()

    def logged_out_buttons(self):
        self.remove_buttons()
        for button_name in self.nav_buttons.keys():
            if button_name == 'Login' or button_name == 'Register':
                button = ButtonTemplate()
                button.text = button_name
                button.icon = self.nav_buttons[button_name]
                button.id = button_name
                button.add_widget(IconLeftWidget(id=button.icon, icon=button.icon))
                self.add_widget(button)

    def remove_buttons(self):
        number_of_kids = range(len(self.children))
        for i in number_of_kids:
            self.remove_widget(self.children[0])

    def logged_in_buttons(self):
        self.remove_buttons()
        for button_name in self.nav_buttons.keys():
            if button_name != 'Login' and button_name != 'Register':
                button = ButtonTemplate()
                button.text = button_name
                button.icon = self.nav_buttons[button_name]
                button.id = button_name
                button.add_widget(IconLeftWidget(id=button.icon, icon=button.icon))
                self.add_widget(button)     

class MainApp(MDApp):
    def __init__(self, **kwargs):
        self.title = "Arhat"
        self.theme_cls.primary_palette = "BlueGray"
        super().__init__(**kwargs)

    def build(self):
        return Builder.load_file("arhat.kv")

if __name__ == "__main__":
    MainApp().run()