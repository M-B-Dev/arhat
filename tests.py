from datetime import datetime, timedelta

import json

import unittest

from app.models import User, Post, Message

from app.auth.forms import LoginForm, RegistrationForm

from app.sn.forms import SearchForm, UpdateAccountForm

from app.main.forms import DateForm, TaskForm

from app.main.routes import(
    set_date, 
    convert_date_format,
    check_depression,
    check_if_depression_sent
    )

from app import create_app, db


from config import Config


date = datetime.strftime(datetime.utcnow().date(), "%Y-%m-%d %H:%M:%S")

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SERVER_NAME = 'localhost.localdomain:5000'
    _external = False
    WTF_CSRF_ENABLED = False


class UserModelCase(unittest.TestCase):
    """Test suite."""

    def setUp(self):
        """Initializes database."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.app.test_client()
        
        db.create_all()


    def tearDown(self):
        """Deletes database."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def test_password_hashing(self):
        """Creates user, checks an incorrect then correct password."""
        u = User(username='susan')
        u.set_password('cat')
        
        self.assertFalse(u.check_password('dog'))
        self.assertTrue(u.check_password('cat'))


    def test_follow(self):
        """Sets up 2 users and mutually follows."""
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()

        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

        u1.pend(u2)
        db.session.commit()
        
        self.assertTrue(u1.is_pending(u2))
        self.assertEqual(u1.pended.count(), 1)
        self.assertEqual(u1.pended.first().username, 'susan')
        self.assertEqual(u2.penders.count(), 1)
        self.assertEqual(u2.penders.first().username, 'john')

        u1.unpend(u2)
        db.session.commit()

        self.assertFalse(u1.is_pending(u2))
        self.assertEqual(u1.pended.count(), 0)
        self.assertEqual(u2.penders.count(), 0)

        u1.follow(u2)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, 'susan')
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, 'john')

        u1.unfollow(u2)
        db.session.commit()

        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_send_and_receive_message(self):
        """This sends a message."""
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add_all([u1, u2])

        msg = Message(author=u1, recipient=u2, body="test")
        db.session.add(msg)
        db.session.commit()
        message = Message.query.filter_by(
            id=u2.messages_received.first().id
            ).first_or_404()

        self.assertEqual(u1.messages_sent.count(), 1)
        self.assertEqual(u2.messages_received.count(), 1)
        self.assertEqual(message.body, "test")

    def test_search_contacts_by_username(self):
        """This searches the database for users by username."""
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add_all([u1, u2])

        people_id = User.query.filter(
            User.id != u1.id
            ).filter(
                User.username.like('%' + "u2" + '%')
                )
        people_email = User.query.filter(
            User.id != u1.id).filter(
                User.email.like('%' + "" + '%')
                )
        people = [person_id for person_id in people_id \
            if person_email.id != u1.id]
        [people.append(person_email) for person_email in people_email \
            if person_email.id != u1.id]
        people = list(dict.fromkeys(people))

        self.assertEqual(len(people), 1)

    def test_search_contacts_by_email(self):
        """This searches the database for users by email."""
        u1 = User(username='john', email='john@example.com')
        u2 = User(username='susan', email='susan@example.com')
        db.session.add_all([u1, u2])
        people_id = User.query.filter(
            User.id != u1.id
            ).filter(
                User.username.like('%' + "" + '%')
                )
        people_email = User.query.filter(
            User.id != u1.id).filter(
                User.email.like('%' + "susan@example.com" + '%')
                )
        people = [person_id for person_id in people_id \
            if person_id.id != u1.id]
        [people.append(person_email) for person_email in people_email \
            if person_email.id != u1.id]
        people = list(dict.fromkeys(people))

        all_people = User.query.filter(
            User.id != u1.id
            ).order_by(
                User.username
                )

        self.assertEqual(len(people), 1)
        self.assertEqual(all_people.count(), 1)

    def test_reset_password_token(self):
        """This checks that the password token is generated."""
        u1 = User(username='john', email='john@example.com')
        db.session.add(u1)
        db.session.commit()
        token = u1.get_reset_password_token()

        self.assertIsNotNone(u1.verify_reset_password_token(token))

    def test_friend_request_token(self):
        """This checks that a fried request token is generated."""
        u1 = User(username='john', email='john@example.com')
        db.session.add(u1)
        db.session.commit()
        token = u1.get_follow_request_token()

        self.assertIsNotNone(u1.verify_follow_request_token(token))

    def test_edit_user_profile(self):
        """This checks that a user'd profile can be succesfully edited."""
        u1 = User(username='john', email='john@example.com')
        db.session.add(u1)
        db.session.commit()
        u1.threshold = 100
        u1.days = 7
        u1.username = 'user1'
        u1.email = "dave@example.com"
        db.session.commit()

        self.assertEqual(u1.threshold, 100)
        self.assertEqual(u1.days, 7)
        self.assertEqual(u1.username, 'user1')
        self.assertEqual(u1.email, "dave@example.com")

    def test_set_date(self):
        """This tests that a date can be set correctly."""
        date = convert_date_format(datetime.utcnow())
        date_object = datetime.strptime("01-01-2001", "%d-%m-%Y")

        self.assertEqual(set_date("ph"), date)
        self.assertEqual(set_date("01-01-2001"), date_object)
    
    def test_check_if_depression_sent(self):
        """This tests that depression check is called correctly."""
        u1 = User(username='john', email='john@example.com')
        db.session.add(u1)
        db.session.commit()

        #checks that without a sent date depression_check will not be run
        self.assertIsNone(check_if_depression_sent(date, u1))

        u1.sent_date = date
        db.session.commit()

        #checks that without threshold or days depression_check won't run
        self.assertIsNone(check_if_depression_sent(date, u1))
    
    def test_login_page(self):
        """This tests login page renders correctly."""
        tester = self.app.test_client()
        response = tester.get('auth/login', content_type="html/text")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            b'Sign In'
            and b'username'
            and b'Password'
            and b'Remember Me'
            and b'Forgot Your Password?'
            and b'Click to Reset It'
            and b'New User?'
            and b'Register!'
            in response.data
        )

    def test_registration(self):
        """Tests after registration there is user in db with correct name."""
        tester = self.app.test_client()
        form = RegistrationForm()
        form.username.data = 'test'
        form.email.data = 'test@test.com'
        form.password.data = 'Password1'
        form.password2.data = 'Password1'
        response = tester.post(
            'auth/register', 
            data=form.data, 
            follow_redirects=False
            )

        self.assertEqual(User.query.all()[0].username, 'test')

    def test_login_functionality(self):
        """Tests that a user can log in and that logut button renders."""
        tester = self.app.test_client()
        response = login_helper(self, tester)

        self.assertIn(b'Logout', response.data)

    def test_logout_functionality(self):
        """Tests that after logout login page is rendered correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        response = tester.get(
            'auth/logout', 
            follow_redirects=True
            )

        self.assertIn(
            b'Sign In'
            and b'username'
            and b'Password'
            and b'Remember Me'
            and b'Forgot Your Password?'
            and b'Click to Reset It'
            and b'New User?',
            response.data
            )   
    
    def test_change_date_functionality(self):
        """Tests that change date renders a page with at the date 01-01-01."""
        tester = self.app.test_client()
        response = login_helper(self, tester)
        form = DateForm()
        form.datepicker.data = datetime.strptime("01-01-01", '%d-%m-%y')
        response = tester.post(
            'index/ph', 
            data=form.data,
            follow_redirects=True
            )

        self.assertIn(b"01-01-01", response.data)

    def test_contacts(self):
        """Tests that users are rendered on contacts page correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username='dave').first()
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mark', email='mark@example.com')
        db.session.add_all([u2, u3])
        db.session.commit()
        response = tester.get('contacts', follow_redirects=True)

        #checks susan and follow option is displayed
        self.assertIn(
            b'susan'
            and b'Last seen on:'
            and b'Follow',
            response.data
            )

        u1.pend(u2)
        response = tester.get('contacts', follow_redirects=True)

        #checks mark and pending is displayed
        self.assertIn(
            b'mark'
            and b'Last seen on:'
            and b'Pending',
            response.data
            )

        u1.follow(u2)
        response = tester.get('contacts', follow_redirects=True)

        #checks susan and following is displayed
        self.assertIn(
            b'susan'
            and b'Last seen on:'
            and b'following'
            and bytes(str(datetime.utcnow().date().day), encoding='utf-8'),
            response.data
            )

        form = SearchForm()
        form.search.data = "susa"
        response = tester.post('contacts', 
            data=form.data,
            follow_redirects=True
            )

        #checks susan is displayed and that mark is not after search for username
        self.assertIn(b'susan', response.data)
        self.assertNotIn(b'mark', response.data)

        form.search.data = 'mark@example.co'
        response = tester.post(
            'contacts', 
            data=form.data,
            follow_redirects=True
            )

        #checks susan is not displayed but that mark is after search for email
        self.assertNotIn(b'susan', response.data)
        self.assertIn(b'mark', response.data)

        u4 = User(username='Ytest', email='Y@example.com')
        u5 = User(username='Xtest', email='X@example.com')
        u6 = User(username='Ztest', email='Z@example.com')
        u7 = User(username='Wtest', email='W@example.com')
        db.session.add_all([u4, u5, u6, u7])
        db.session.commit()
        response = tester.get('contacts?page=2', follow_redirects=True)

        #checks susan is displayed and mark is not on page 2 of paginated contacts 
        self.assertIn(b'susan', response.data)
        self.assertNotIn(b'mark', response.data)

    def test_messages(self):
        """Tests sending, receiving and replying to messages."""
        tester = self.app.test_client()
        login_helper(self, tester)
        response = tester.get('messages', follow_redirects=True)

        #checks received messages is rendered correctly
        self.assertIn(b'Received Messages', response.data)

        u1 = User.query.filter_by(username='dave').first()
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u2)
        db.session.commit()
        for i in range(6):
            msg = Message(author=u2, recipient=u1,body="test")
            db.session.add(msg)
        db.session.commit()
        db.session.flush()
        ident = msg.id
        response = tester.get('messages', follow_redirects=True)

        #checks susan's message is rendered correctly
        self.assertIn(b'susan said'and b'test', response.data)

        response = tester.get('messages?page=2', follow_redirects=True)

        #checks susan's message is rendered correctly on page 2
        self.assertIn(b'susan said' and b'test', response.data)

        response = tester.get('messages?page=1', follow_redirects=True)

        #checks susan's message is rendered correctly on page 1
        self.assertIn(b'susan said'and b'test', response.data)

        response = tester.get(
            f'reply/{u2.username}/{ident}', 
            follow_redirects=True
            )

        #checks reply renderes with correct quotation text
        self.assertIn(
            b'Quote: test, sent on'
            and bytes(str(datetime.utcnow().date().year), encoding='utf-8')
            and b'Message to susan', 
            response.data
            )

        for i in range(6):
            msg = Message(author=u1, recipient=u2, body="sent test")
            db.session.add(msg)
        db.session.commit()
        response = tester.get('sent_messages', follow_redirects=True)

        #checks sent message is rendered correctly
        self.assertIn(
            b'You sent susan the message'
            and b'sent test', 
            response.data
            )

        response = tester.get('sent_messages?page=2', follow_redirects=True)

        #checks sent message is rendered correctly on page 2
        self.assertIn(b'You sent susan the message', response.data)

    def test_edit_profile(self):
        """Tests changing profile data."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username='dave').first()
        u1.threshold = 99999999
        u1.days = 7
        db.session.commit()
        response = tester.get('edit_profile', follow_redirects=True)

        #checks user data is is rendered correctly
        self.assertIn(
            b'User:'
            and bytes(u1.username, encoding='utf-8')
            and bytes(u1.email, encoding='utf-8')
            and bytes(str(datetime.utcnow().date().year), encoding='utf-8')
            and b'99999999'
            and b'7'
            and b'Enable Push Messaging',   
            response.data
            )

        form = UpdateAccountForm()
        form.threshold.data = 100
        form.days.data = 14
        form.username.data = 'testest'
        form.email.data = 'testtest@testtest.com'
        response = tester.post(
        'edit_profile',
        data=form.data, 
        follow_redirects=True
        )
        
        #checks changes in user data are rendered correctly
        self.assertIn(
            b'testtest'
            and b'testtest@testtest.com'
            and b'100'
            and b'14',
            response.data)

    def test_adding_editing_and_removing_tasks(self):
        """Tests changing profile data."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username='dave').first()
        new_task = Post(
            body='This is a test task',
            done=False,
            start_time=0,
            end_time=1000,
            date=datetime.strptime(date, "%Y-%m-%d %H:%M:%S"),
            hour=datetime.utcnow().hour,
            user_id=u1.id,
            frequency=0,
            color='#fff'
            )
        db.session.add(new_task)
        db.session.commit()
        task = Post.query.first()
        response = tester.post('index/ph', follow_redirects=True)

        #Check the new task has been rendered correctly on the correct date
        self.assertIn(b'This is a test task', response.data)

        task.frequency = 2
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") \
            - timedelta(days=1)
        db.session.commit()
        response = tester.post('index/ph', follow_redirects=True)

        #checks that a frequency change has meant the task is not 
        #rendered on a specific date
        self.assertNotIn(b'This is a test task', response.data)

        task.frequency = 1
        db.session.commit()
        response = tester.post('index/ph', follow_redirects=True)

        #checks that a further frequency change has meant the task is  
        #rendered on a specific date
        self.assertIn(b'This is a test task', response.data)

        task.done = True
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        db.session.commit()
        response = tester.post('index/ph',follow_redirects=True)

        #checks a completed task is not rendered
        self.assertNotIn(
            b'This is a test task', response.data
            )

        task.done = False
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") \
            - timedelta(days=10)
        db.session.commit()
        new_task = Post(
            body='This is an edited, single event test task',
            done=False,
            start_time=1001,
            end_time=1400,
            date=datetime.strptime(date, "%Y-%m-%d %H:%M:%S"),
            hour=datetime.utcnow().hour,
            user_id=u1.id,
            frequency=0,
            color='#fff',
            exclude=task.id
            )
        task.exclude = task.id
        db.session.add(new_task)
        db.session.commit()
        response = tester.post('index/ph', follow_redirects=True)

        #checks that a frequency task edit of a single event is rendered correctly
        #and that the frequency task is not rendered. 
        self.assertNotIn(b'This is a test task', response.data)
        self.assertIn(
            b'This is an edited, single event test task',
            response.data
            )

        form = TaskForm()
        form.task.data = "This is a single task"
        form.start_time.data = datetime.now().strftime("%H:%M")
        form.end_time.data = datetime.now().strftime("%H:%M")
        form.date.data = date
        form.color.data = "#fff"
        form.frequency.data = 0
        form.single_event.data = None
        response = tester.post(
            '/new_task/', 
            data=form.data
            )
        converted_response_data = json.loads(response.data)
        form.ident.data = converted_response_data['id']
        response = tester.post('index/ph',follow_redirects=True)

        #Checks that a single new task is created 
        self.assertIn(
            b"This is a single task",
            response.data
            )

        form.task.data = "This is a new task"
        form.done.data = None
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post('index/ph',follow_redirects=True)

        #Checks that a single new task has been edited 
        self.assertIn(
            b"This is a new task",
            response.data
            )
        
        form.frequency.data = 1
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        tomorrow = datetime.strftime(
            datetime.utcnow().date() + timedelta(days=1), 
            "%d-%m-%Y"
            )
        response = tester.post(f'index/{tomorrow}', follow_redirects=True)
        
        #Checks that the new task is now a frequency task 
        self.assertIn(b"This is a new task", response.data)
        
        day_b4_yesterday = datetime.strftime(
            datetime.utcnow().date() - timedelta(days=1), 
            "%d-%m-%Y"
            )
        response = tester.post(
            f'index/{day_b4_yesterday}', 
            follow_redirects=True
            )
        
        #Checks that the new task is a frequency task and is not on a prior date
        self.assertNotIn(
            b"This is a new task",
            response.data
            )

        formatted_tomorrow = datetime.strftime(
            datetime.utcnow().date() + timedelta(days=1), 
            "%Y-%m-%d %H:%M:%S"
            )
        form.task.data = "This is an edit of a freq task"
        form.date.data = formatted_tomorrow
        form.single_event.data = True
        form.done.data = None
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/{tomorrow}', follow_redirects=True)
        
        #Checks that the new task is a frequency task 
        self.assertIn(b"This is an edit of a freq task", response.data)

        form.ident.data = 4
        form.single_event.data = None
        form.frequency.data = 2
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/{tomorrow}', follow_redirects=True)
        
        #Checks that the a frequency change from a child task 
        #that results in the child task falling outside of the frequency 
        #dates will hide the task
        self.assertNotIn(b"This is an edit of a freq task", response.data)

        form.ident.data = converted_response_data['id']
        form.frequency.data = 1
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/{tomorrow}', follow_redirects=True)
        
        #Checks that a subsequent change on freq from the parent task  
        #impacts the child too (potentially displaying, as in this case, 
        #when previosuly it was hidden)
        self.assertIn(b"This is an edit of a freq task", response.data)

        form.ident.data = 4
        form.task.data = "Edit on all related tasks from a child task"
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/ph', follow_redirects=True)

        #checks that an edit on a child task for all will impact all tasks
        self.assertIn(
            b"Edit on all related tasks from a child task", 
            response.data
            )

        form.ident.data = converted_response_data['id']
        form.single_event.data = True
        form.task.data = "This is an edit of the original freq task"
        form.date.data = date
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/ph', follow_redirects=True)
        
        #Checks that the original task can be independently edited 
        self.assertIn(
            b"This is an edit of the original freq task", 
            response.data
            )
        
        form.ident.data = 4
        form.date.data = formatted_tomorrow
        form.done.data = True
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/{tomorrow}', follow_redirects=True)

        # Query to find task id: Post.query.filter_by(body="").first().id
        #Checks that the edited freq task has been completed and 
        # is not diplayed
        self.assertNotIn(b"This is an edit of a freq task", response.data)
       
        form.ident.data = converted_response_data['id']
        form.done.data = True
        form.single_event.data = None
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/ph', follow_redirects=True)

        #checks that a parent task can impact all tasks when set to done
        self.assertNotIn(
            b"This is an edit of the original freq task", 
            response.data
            )

        form = TaskForm()
        form.task.data = "This is a time limited freq task"
        form.start_time.data = datetime.now().strftime("%H:%M")
        form.end_time.data = datetime.now().strftime("%H:%M")
        form.date.data = date
        form.color.data = "#fff"
        form.frequency.data = 1
        form.single_event.data = None
        form.to_date.data = tomorrow
        response = tester.post(
            '/new_task/', 
            data=form.data
            )
        converted_response_data = json.loads(response.data)
        form.ident.data = int(converted_response_data['id'])
        response = tester.post('index/ph',follow_redirects=True)


        #Checks that a freq time limited task is created 
        self.assertIn(
            b"This is a time limited freq task",
            response.data
            )

        response = tester.post(f'index/{tomorrow}',follow_redirects=True)

        #Checks that a freq time limited task appears tomorrow 
        self.assertIn(
            b"This is a time limited freq task",
            response.data
            )

        day_after_tomorrow = datetime.strftime(
            datetime.utcnow().date() + timedelta(days=2), 
            "%d-%m-%Y"
            )
        response = tester.post(
            f'index/{day_after_tomorrow}',
            follow_redirects=True
            )

        #Checks freq time limited task does not appear day after tomorrow
        self.assertNotIn(
            b"This is a time limited freq task",
            response.data
            )
        
        form.done.data = None
        form.date.data = formatted_tomorrow
        form.single_event.data = True
        form.task.data = "this is an edited single event of a time limited freq task"
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/{tomorrow}',follow_redirects=True)

        #Checks that an edited single freq time limited task appears tomorrow 
        self.assertIn(
            b"this is an edited single event of a time limited freq task",
            response.data
            )
        
        form.single_event.data = None
        form.date.data = date
        form.done.data = True
        response = tester.post(
            '/edit_task/', 
            data=form.data
            )
        response = tester.post(f'index/{tomorrow}',follow_redirects=True)

        #Checks that a freq time limited task does not appear tomorrow 
        self.assertNotIn(
            b"this is an edited single event of a time limited freq task",
            response.data
            )
        
        response = tester.post(f'index/ph',follow_redirects=True)

        #Checks that a freq time limited task does not appear today 
        self.assertNotIn(
            b"this is an edited single event of a time limited freq task",
            response.data
            )
        
def login_helper(self, client):
    """Helper to register and log in a user to the db."""
    u1 = User(username='dave', email='john@example.com')
    db.session.add(u1)
    u1.set_password("test")
    db.session.commit()
    form = LoginForm()
    form.username.data = "dave"
    form.password.data = "test"
    response = client.post(
        'auth/login', 
        data=form.data,
        follow_redirects=True
        )
    return response

if __name__ == '__main__':
    unittest.main(verbosity=2)