from datetime import datetime, timedelta

import unittest

from app.models import User, Post, Message

from app.auth.forms import LoginForm, RegistrationForm

from app.sn.forms import SearchForm, MessageForm, UpdateAccountForm

from app.main.forms import DateForm, TaskForm

from app.main.routes import(
    set_date, 
    convert_date_format,
    check_depression_on_index,
    check_depression
    )

from app import create_app, db

import json

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
        u1 = User(username='john', email='john@example.com')
        db.session.add(u1)
        db.session.commit()

        token = u1.get_reset_password_token()
        self.assertIsNotNone(u1.verify_reset_password_token(token))

    def test_friend_request_token(self):
        u1 = User(username='john', email='john@example.com')
        db.session.add(u1)
        db.session.commit()

        token = u1.get_follow_request_token()
        self.assertIsNotNone(u1.verify_follow_request_token(token))

    def test_edit_user_profile(self):
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
        date = convert_date_format(datetime.utcnow())
        date_object = datetime.strptime("01-01-2001", "%d-%m-%Y")
        self.assertEqual(set_date("ph"), date)
        self.assertEqual(set_date("01-01-2001"), date_object)
    
    def test_check_depression_on_index(self):
        u1 = User(username='john', email='john@example.com')
        db.session.add(u1)
        db.session.commit()
    
        self.assertIsNone(check_depression_on_index(date, u1))
        u1.sent_date = date
        self.assertIsNone(check_depression_on_index(date, u1))
    
    def test_login_page(self):
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
        tester = self.app.test_client()
        response = login_helper(self, tester)
        self.assertIn(b'Logout', response.data)

    def test_logout_functionality(self):
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
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username='dave').first()
        u2 = User(username='susan', email='susan@example.com')
        u3 = User(username='mark', email='mark@example.com')
        db.session.add_all([u2, u3])
        db.session.commit()
        response = tester.get(
        'contacts', 
        follow_redirects=True
        )
        self.assertIn(
            b'susan'
            and b'Last seen on:'
            and b'Follow',
            response.data
        )
        u1.pend(u2)
        response = tester.get(
        'contacts', 
        follow_redirects=True
        )
        self.assertIn(
            b'mark'
            and b'Last seen on:'
            and b'Pending',
            response.data
        )
        u1.follow(u2)
        response = tester.get(
        'contacts', 
        follow_redirects=True
        )
        self.assertIn(
            b'susan'
            and b'Last seen on:'
            and b'following'
            and bytes(str(datetime.utcnow().date().day), encoding='utf-8'),
            response.data
        )
        form = SearchForm()
        form.search.data = "susa"
        response = tester.post(
        'contacts', 
        data=form.data,
        follow_redirects=True
        )
        self.assertIn(b'susan', response.data)
        self.assertNotIn(b'mark', response.data)
        form.search.data = 'mark@example.co'
        response = tester.post(
        'contacts', 
        data=form.data,
        follow_redirects=True
        )
        self.assertNotIn(b'susan', response.data)
        self.assertIn(b'mark', response.data)
        u4 = User(username='Ytest', email='Y@example.com')
        u5 = User(username='Xtest', email='X@example.com')
        u6 = User(username='Ztest', email='Z@example.com')
        u7 = User(username='Wtest', email='W@example.com')
        db.session.add_all([u4, u5, u6, u7])
        db.session.commit()
        response = tester.get(
        'contacts?page=2', 
        follow_redirects=True
        )
        self.assertIn(b'susan', response.data)
        self.assertNotIn(b'mark', response.data)

    def test_messages(self):
        tester = self.app.test_client()
        login_helper(self, tester)
        response = tester.get(
        'messages', 
        follow_redirects=True
        )
        self.assertIn(b'Received Messages', response.data)
        u1 = User.query.filter_by(username='dave').first()
        u2 = User(username='susan', email='susan@example.com')
        db.session.add(u2)
        db.session.commit()
        for i in range(6):
            msg = Message(
            author=u2, 
            recipient=u1,
            body="test"
            )
            db.session.add(msg)
        db.session.commit()
        db.session.flush()
        ident = msg.id
        response = tester.get('messages', follow_redirects=True)
        self.assertIn(b'susan said'and b'test', response.data)
        response = tester.get(
        'messages?page=2', 
        follow_redirects=True
        )
        self.assertIn(
            b'susan said'
            and b'test', 
            response.data)
        response = tester.get(
        'messages?page=1', 
        follow_redirects=True
        )
        self.assertIn(
            b'susan said'
            and b'test', 
            response.data)
        response = tester.get(
        f'reply/{u2.username}/{ident}', 
        follow_redirects=True
        )
        self.assertIn(
            b'Quote: test, sent on'
            and bytes(str(datetime.utcnow().date().year), encoding='utf-8')
            and b'Message to susan', 
            response.data)
        for i in range(6):
            msg = Message(
            author=u1, 
            recipient=u2,
            body="sent test"
            )
            db.session.add(msg)
        db.session.commit()
        response = tester.get(
        'sent_messages', 
        follow_redirects=True
        )
        self.assertIn(
            b'You sent susan the message'
            and b'sent test', 
            response.data)
        response = tester.get(
        'sent_messages?page=2', 
        follow_redirects=True
        )
        self.assertIn(
            b'You sent susan the message', 
            response.data)

    def test_edit_profile(self):
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username='dave').first()
        u1.threshold = 99999999
        u1.days = 7
        db.session.commit()
        response = tester.get(
        'edit_profile', 
        follow_redirects=True
        )    
        self.assertIn(
            b'User:'
            and bytes(u1.username, encoding='utf-8')
            and bytes(u1.email, encoding='utf-8')
            and bytes(str(datetime.utcnow().date().year), encoding='utf-8')
            and b'99999999'
            and b'7'
            and b'Enable Push Messaging',   
            response.data)
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
        self.assertIn(
            b'testtest'
            and b'testtest@testtest.com'
            and b'100'
            and b'14',
            response.data)

    def test_adding_editing_and_removing_tasks(self):
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
        response = tester.post(
            'index/ph',
            follow_redirects=True
            )
        self.assertIn(
            b'This is a test task',
            response.data)
        task.frequency = 2
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") - timedelta(days=1)
        db.session.commit()
        response = tester.post(
            'index/ph',
            follow_redirects=True
            )
        self.assertNotIn(
            b'This is a test task',
            response.data)
        task.frequency = 1
        db.session.commit()
        response = tester.post(
            'index/ph',
            follow_redirects=True
            )
        self.assertIn(
            b'This is a test task',
            response.data)
        task.done = True
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        db.session.commit()
        response = tester.post(
            'index/ph',
            follow_redirects=True
            )
        self.assertNotIn(
            b'This is a test task',
            response.data)
        task.done = False
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") - timedelta(days=10)
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
        response = tester.post(
            'index/ph',
            follow_redirects=True
            )
        self.assertNotIn(
            b'This is a test task',
            response.data)
        self.assertIn(
            b'This is an edited, single event test task',
            response.data)
        form = TaskForm()
        form.task.data

def login_helper(self, client):
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