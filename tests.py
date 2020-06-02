from datetime import datetime, timedelta

import json

import unittest

from app.models import User, Post, Message

from app.auth.forms import LoginForm, RegistrationForm

from app.sn.forms import SearchForm, UpdateAccountForm

from app.main.forms import DateForm, TaskForm

from app.main.routes import (
    set_date,
    convert_date_format
)

from app import create_app, db


from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    SERVER_NAME = "localhost.localdomain:5000"
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
        u = User(username="susan")
        u.set_password("cat")

        self.assertFalse(u.check_password("dog"))
        self.assertTrue(u.check_password("cat"))

    def test_followed(self):
        """Sets up 2 users and checks followed."""
        u1, u2 = user_creation_helper(self)

        self.assertEqual(u1.followed.all(), [])
        self.assertEqual(u1.followers.all(), [])

    def test_pend(self):
        """Sets up 2 users and checks pend."""
        u1, u2 = user_creation_helper(self)

        u1.pend(u2)
        db.session.commit()

        self.assertTrue(u1.is_pending(u2))
        self.assertEqual(u1.pended.count(), 1)
        self.assertEqual(u1.pended.first().username, "susan")
        self.assertEqual(u2.penders.count(), 1)
        self.assertEqual(u2.penders.first().username, "john")

    def test_unpend(self):
        """Sets up 2 users and checks unpend."""
        u1, u2 = user_creation_helper(self)
        u1.pend(u2)
        db.session.commit()

        u1.unpend(u2)
        db.session.commit()

        self.assertFalse(u1.is_pending(u2))
        self.assertEqual(u1.pended.count(), 0)
        self.assertEqual(u2.penders.count(), 0)

    def test_follow(self):
        """Sets up 2 users and checks follow."""
        u1, u2 = user_creation_helper(self)

        u1.follow(u2)
        db.session.commit()

        self.assertTrue(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 1)
        self.assertEqual(u1.followed.first().username, "susan")
        self.assertEqual(u2.followers.count(), 1)
        self.assertEqual(u2.followers.first().username, "john")

    def test_unfollow(self):
        """Sets up 2 users and checks unfollow."""
        u1, u2 = user_creation_helper(self)
        u1.follow(u2)
        db.session.commit()

        u1.unfollow(u2)
        db.session.commit()

        self.assertFalse(u1.is_following(u2))
        self.assertEqual(u1.followed.count(), 0)
        self.assertEqual(u2.followers.count(), 0)

    def test_send_and_receive_message(self):
        """This sends a message."""
        u1 = User(username="john", email="john@example.com")
        u2 = User(username="susan", email="susan@example.com")
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
        u1 = User(username="john", email="john@example.com")
        u2 = User(username="susan", email="susan@example.com")
        db.session.add_all([u1, u2])

        people_id = User.query.filter(User.id != u1.id).filter(
            User.username.like("%" + "u2" + "%")
        )
        people_email = User.query.filter(User.id != u1.id).filter(
            User.email.like("%" + "" + "%")
        )
        people = [person_id for person_id in people_id if person_email.id != u1.id]
        [
            people.append(person_email)
            for person_email in people_email
            if person_email.id != u1.id
        ]
        people = list(dict.fromkeys(people))

        self.assertEqual(len(people), 1)

    def test_search_contacts_by_email(self):
        """This searches the database for users by email."""
        u1 = User(username="john", email="john@example.com")
        u2 = User(username="susan", email="susan@example.com")
        db.session.add_all([u1, u2])
        people_id = User.query.filter(User.id != u1.id).filter(
            User.username.like("%" + "" + "%")
        )
        people_email = User.query.filter(User.id != u1.id).filter(
            User.email.like("%" + "susan@example.com" + "%")
        )
        people = [person_id for person_id in people_id if person_id.id != u1.id]
        [
            people.append(person_email)
            for person_email in people_email
            if person_email.id != u1.id
        ]
        people = list(dict.fromkeys(people))

        all_people = User.query.filter(User.id != u1.id).order_by(User.username)

        self.assertEqual(len(people), 1)
        self.assertEqual(all_people.count(), 1)

    def test_reset_password_token(self):
        """This checks that the password token is generated."""
        u1 = User(username="john", email="john@example.com")
        db.session.add(u1)
        db.session.commit()
        token = u1.get_reset_password_token()

        self.assertIsNotNone(u1.verify_reset_password_token(token))

    def test_friend_request_token(self):
        """This checks that a fried request token is generated."""
        u1 = User(username="john", email="john@example.com")
        db.session.add(u1)
        db.session.commit()
        token = u1.get_follow_request_token()

        self.assertIsNotNone(u1.verify_follow_request_token(token))

    def test_edit_user_profile(self):
        """This checks that a user'd profile can be succesfully edited."""
        u1 = User(username="john", email="john@example.com")
        db.session.add(u1)
        db.session.commit()
        u1.threshold = 100
        u1.days = 7
        u1.username = "user1"
        u1.email = "dave@example.com"
        db.session.commit()

        self.assertEqual(u1.threshold, 100)
        self.assertEqual(u1.days, 7)
        self.assertEqual(u1.username, "user1")
        self.assertEqual(u1.email, "dave@example.com")

    def test_set_date(self):
        """This tests that a date can be set correctly."""
        date = convert_date_format(datetime.utcnow())
        date_object = datetime.strptime("01-01-2001", "%d-%m-%Y")

        self.assertEqual(set_date("ph"), date)
        self.assertEqual(set_date("01-01-2001"), date_object)

    def test_check_if_depression_sent_date(self):
        """checks that with a sent date depression_check will not be run."""
        u1 = User(username="john", email="john@example.com")
        db.session.add(u1)
        db.session.commit()

        self.assertIsNone(u1.check_if_depression_sent(date))

    def test_check_if_depression_sent_date(self):
        """checks that without threshold or days depression_check won't run."""
        u1 = User(username="john", email="john@example.com")
        db.session.add(u1)
        u1.sent_date = date
        db.session.commit()

        self.assertIsNone(u1.check_if_depression_sent(date))

    def test_login_page(self):
        """This tests login page renders correctly."""
        tester = self.app.test_client()
        response = tester.get("login_page", content_type="html/text")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            b"Sign In"
            and b"username"
            and b"Password"
            and b"Remember Me"
            and b"Forgot Your Password?"
            and b"Click to Reset It"
            and b"New User?"
            and b"Register!" in response.data
        )

    def test_registration(self):
        """Tests after registration there is user in db with correct name."""
        tester = self.app.test_client()
        form = RegistrationForm()
        form.username.data = "test"
        form.email.data = "test@test.com"
        form.password.data = "Password1"
        form.password2.data = "Password1"
        response = tester.post("register", data=form.data, follow_redirects=False)

        self.assertEqual(User.query.all()[0].username, "test")

    def test_login_functionality(self):
        """Tests that a user can log in and that logut button renders."""
        tester = self.app.test_client()
        response = login_helper(self, tester)

        self.assertIn(b"Logout", response.data)

    def test_logout_functionality(self):
        """Tests that after logout login page is rendered correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        response = tester.get("logout", follow_redirects=True)

        self.assertIn(
            b"Sign In"
            and b"username"
            and b"Password"
            and b"Remember Me"
            and b"Forgot Your Password?"
            and b"Click to Reset It"
            and b"New User?",
            response.data,
        )

    def test_change_date_functionality(self):
        """Tests that change date renders a page with at the date 01-01-01."""
        tester = self.app.test_client()
        response = login_helper(self, tester)
        form = DateForm()
        form.datepicker.data = datetime.strptime("01-01-01", "%d-%m-%y")
        response = tester.post("index/ph", data=form.data, follow_redirects=True)

        self.assertIn(b"01-01-01", response.data)

    def test_contacts_follow(self):
        """Tests that followed users are rendered on contacts page correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, u3 = contacts_helper(self)

        response = tester.get("contacts", follow_redirects=True)

        self.assertIn(b"susan" and b"Last seen on:" and b"Follow", response.data)

    def test_contacts_pending(self):
        """Tests that pending users are rendered on contacts page correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, u3 = contacts_helper(self)

        u1.pend(u2)
        response = tester.get("contacts", follow_redirects=True)

        self.assertIn(b"mark" and b"Last seen on:" and b"Pending", response.data)

    def test_contacts_following(self):
        """Tests that following users are rendered on contacts page correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, u3 = contacts_helper(self)

        u1.follow(u2)
        response = tester.get("contacts", follow_redirects=True)

        self.assertIn(
            b"susan"
            and b"Last seen on:"
            and b"following"
            and bytes(str(datetime.utcnow().date().day), encoding="utf-8"),
            response.data,
        )

    def test_contacts_search_username(self):
        """Tests that susan is displayed and that mark is not after search for username."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, u3 = contacts_helper(self)

        form = SearchForm()
        form.search.data = "susa"
        response = tester.post("contacts", data=form.data, follow_redirects=True)

        self.assertIn(b"susan", response.data)
        self.assertNotIn(b"mark", response.data)

    def test_contacts_search_email(self):
        """Tests susan is not displayed but that mark is after search for email."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, u3 = contacts_helper(self)
        form = SearchForm()
        form.search.data = "mark@example.co"
        response = tester.post("contacts", data=form.data, follow_redirects=True)

        self.assertNotIn(b"susan", response.data)
        self.assertIn(b"mark", response.data)

    def test_contacts_pagination(self):
        """Tests susan is displayed and mark is not on page 2 of paginated contacts."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, u3 = contacts_helper(self)
        u4 = User(username="Ytest", email="Y@example.com")
        u5 = User(username="Xtest", email="X@example.com")
        u6 = User(username="Ztest", email="Z@example.com")
        u7 = User(username="Wtest", email="W@example.com")
        db.session.add_all([u4, u5, u6, u7])
        db.session.commit()
        response = tester.get("contacts?page=2", follow_redirects=True)

        self.assertIn(b"susan", response.data)
        self.assertNotIn(b"mark", response.data)

    def test_messages_received_page(self):
        """Tests received messages page is rendered correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        response = tester.get("messages", follow_redirects=True)

        self.assertIn(b"Received Messages", response.data)

    def test_messages_received(self):
        """Tests received message is rendered correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, ident = message_helper(self)

        response = tester.get("messages", follow_redirects=True)
        self.assertIn(b"susan said" and b"test", response.data)

    def test_messages_received_pagination_2(self):
        """Tests receieved message is rendered correctly on page 2."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, ident = message_helper(self)

        response = tester.get("messages?page=2", follow_redirects=True)
        self.assertIn(b"susan said" and b"test", response.data)

    def test_messages_received_pagination_1(self):
        """Tests receieved message is rendered correctly on page 1."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, ident = message_helper(self)
        response = tester.get("messages?page=1", follow_redirects=True)

        self.assertIn(b"susan said" and b"test", response.data)

    def test_messages_received_reply_format(self):
        """Tests reply is rendered correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, ident = message_helper(self)

        response = tester.get(f"reply/{u2.username}/{ident}", follow_redirects=True)

        self.assertIn(
            b"Quote: test, sent on"
            and bytes(str(datetime.utcnow().date().year), encoding="utf-8")
            and b"Message to susan",
            response.data,
        )

    def test_messages_sent(self):
        """Tests sent message is rendered correctly."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, ident = message_helper(self)

        response = tester.get("sent_messages", follow_redirects=True)

        self.assertIn(b"You sent susan the message" and b"sent test", response.data)

    def test_messages_sent_pagination_2(self):
        """Tests sent message is rendered correctly on page 2."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1, u2, ident = message_helper(self)

        response = tester.get("sent_messages?page=2", follow_redirects=True)

        # checks sent message is rendered correctly on page 2
        self.assertIn(b"You sent susan the message", response.data)

    def test_edit_profile(self):
        """Tests setting profile data from backend."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username="dave").first()
        u1.threshold = 99999999
        u1.days = 7
        db.session.commit()
        response = tester.get("edit_profile", follow_redirects=True)

        self.assertIn(
            b"User:"
            and bytes(u1.username, encoding="utf-8")
            and bytes(u1.email, encoding="utf-8")
            and bytes(str(datetime.utcnow().date().year), encoding="utf-8")
            and b"99999999"
            and b"7"
            and b"Enable Push Messaging",
            response.data,
        )

    def test_edit_profile_form(self):
        """Tests setting profile data from the form."""
        tester = self.app.test_client()
        login_helper(self, tester)

        form = UpdateAccountForm()
        form.threshold.data = 100
        form.days.data = 14
        form.username.data = "testest"
        form.email.data = "testtest@testtest.com"
        response = tester.post("edit_profile", data=form.data, follow_redirects=True)

        self.assertIn(
            b"testtest" and b"testtest@testtest.com" and b"100" and b"14", response.data
        )

    def test_adding_tasks(self):
        """Check the new task has been rendered correctly on the correct date."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username="dave").first()
        add_and_edit_task_helper(self)
        task = Post.query.first()

        response = tester.post("index/ph", follow_redirects=True)

        self.assertIn(b"This is a test task", response.data)

    def test_editing_task_frequency(self):
        """Tests that a frequency change has meant the task is not rendered on a specific date."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username="dave").first()
        add_and_edit_task_helper(self)
        task = Post.query.first()

        task.frequency = 2
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") - timedelta(days=1)
        db.session.commit()
        response = tester.post("index/ph", follow_redirects=True)

        self.assertNotIn(b"This is a test task", response.data)

        task.frequency = 1
        db.session.commit()
        response = tester.post("index/ph", follow_redirects=True)

        self.assertIn(b"This is a test task", response.data)

    def test_editing_task_done(self):
        """Tests that a completed task is not rendered."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username="dave").first()
        add_and_edit_task_helper(self)
        task = Post.query.first()
        task.frequency = 1
        task.done = True
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        db.session.commit()
        response = tester.post("index/ph", follow_redirects=True)

        self.assertNotIn(b"This is a test task", response.data)

    def test_editing_single_freq_task(self):
        """Tests that a frequency task edit of a single event is rendered correctly
            and that the frequency task is not rendered."""
        tester = self.app.test_client()
        login_helper(self, tester)
        u1 = User.query.filter_by(username="dave").first()
        add_and_edit_task_helper(self)
        task = Post.query.first()
        task.frequency = 1
        task.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S") - timedelta(days=10)
        db.session.commit()
        new_task = Post(
            body="This is an edited, single event test task",
            done=False,
            start_time=1001,
            end_time=1400,
            date=datetime.strptime(date, "%Y-%m-%d %H:%M:%S"),
            hour=datetime.utcnow().hour,
            user_id=u1.id,
            frequency=0,
            color="#fff",
            exclude=task.id,
        )
        task.exclude = task.id
        db.session.add(new_task)
        db.session.commit()
        response = tester.post("index/ph", follow_redirects=True)

        self.assertNotIn(b"This is a test task", response.data)
        self.assertIn(b"This is an edited, single event test task", response.data)

    def test_adding_single_task_from_form(self):
        """Tests that a single new task is created from the form."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, _ = new_task_with_form_helper(self, tester)

        response = tester.post("index/ph", follow_redirects=True)

        self.assertIn(b"This is a single task", response.data)

    def test_editing_single_task_from_form(self):
        """Tests that a single new task has been edited."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, _ = new_task_with_form_helper(self, tester)

        form.task.data = "This is a new task"
        form.done.data = None
        response = tester.post("/edit_task/", data=form.data)
        response = tester.post("index/ph", follow_redirects=True)

        self.assertIn(b"This is a new task", response.data)

    def test_editing_single_task_frequency_from_form(self):
        """Tests that a single new task has been edited to now be a frequency task."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, _ = new_task_with_form_helper(self, tester)
        form = form_helper(1, form, tester)

        response = tester.post(f"index/{tomorrow}", follow_redirects=True)
        self.assertIn(b"This is a new task", response.data)

        response = tester.post(f"index/{yesterday}", follow_redirects=True)
        self.assertNotIn(b"This is a new task", response.data)

    def test_editing_frequency_from_form(self):
        """Tests that a single new task has been edited to now be a frequency task."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, _ = new_task_with_form_helper(self, tester)
        form = form_helper(2, form, tester)

        response = tester.post(f"index/{tomorrow}", follow_redirects=True)
        self.assertIn(b"This is an edit of a freq task", response.data)

    def test_editing_frequency_from_child_task(self):
        """Tests that the a frequency change from a child task 
        that results in the child task falling outside of the frequency 
        dates will hide the task."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, _ = new_task_with_form_helper(self, tester)
        form = form_helper(3, form, tester)

        response = tester.post(f"index/{tomorrow}", follow_redirects=True)
        self.assertNotIn(b"This is an edit of a freq task", response.data)

    def test_editing_parent_and_all_child_tasks(self):
        """Tests that a subsequent change on freq from the parent task  
        impacts the child too (potentially displaying, as in this case, 
        when previosuly it was hidden)"""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, converted_response_data = new_task_with_form_helper(self, tester)
        form = form_helper(4, form, tester, ident=converted_response_data["id"])
        response = tester.post(f"index/{tomorrow}", follow_redirects=True)

        self.assertIn(b"This is an edit of a freq task", response.data)

    def test_editing_child_and_all_related_tasks(self):
        """Tests that an edit on a child task for all will impact all tasks"""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, converted_response_data = new_task_with_form_helper(self, tester)
        form = form_helper(5, form, tester, ident=converted_response_data["id"])
        response = tester.post(f"index/ph", follow_redirects=True)
        self.assertIn(b"Edit on all related tasks from a child task", response.data)

    def test_editing_orginal_of_frequency_tasks(self):
        """Tests that the original task can be independently edited."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, converted_response_data = new_task_with_form_helper(self, tester)
        form = form_helper(6, form, tester, ident=converted_response_data["id"])
        response = tester.post(f"index/ph", follow_redirects=True)
        self.assertIn(b"This is an edit of the original freq task", response.data)

    def test_editing_orginal_of_frequency_tasks(self):
        """Tests that the edited freq task has been completed and 
        is not diplayed."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, converted_response_data = new_task_with_form_helper(self, tester)
        form = form_helper(7, form, tester, ident=converted_response_data["id"])

        response = tester.post(f"index/{tomorrow}", follow_redirects=True)

        self.assertNotIn(b"This is an edit of a freq task", response.data)

    def test_editing_orginal_as_done_for_all(self):
        """Tests that a parent task can impact all tasks when set to done."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, converted_response_data = new_task_with_form_helper(self, tester)
        form = form_helper(8, form, tester, ident=converted_response_data["id"])

        response = tester.post(f"index/ph", follow_redirects=True)

        self.assertNotIn(b"This is an edit of the original freq task", response.data)

    def test_time_limited_frequency_task_creation(self):
        """Tests that a freq time limited task is created and appears the following day but doesn't appear after that."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, converted_response_data = new_task_with_form_helper(self, tester)
        form_helper(8, form, tester, ident=converted_response_data["id"])
        form, converted_response_data = new_time_limited_task_helper(self, tester)

        response = tester.post("index/ph", follow_redirects=True)
        self.assertIn(b"This is a time limited freq task", response.data)

        response = tester.post(f"index/{tomorrow}", follow_redirects=True)

        self.assertIn(b"This is a time limited freq task", response.data)

        day_after_tomorrow = datetime.strftime(
            datetime.utcnow().date() + timedelta(days=2), "%d-%m-%Y"
        )
        response = tester.post(f"index/{day_after_tomorrow}", follow_redirects=True)

        self.assertNotIn(b"This is a time limited freq task", response.data)

    def test_time_limited_frequency_task_edit(self):
        """Tests that an edited single freq time limited task appears tomorrow."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, converted_response_data = new_task_with_form_helper(self, tester)
        form_helper(8, form, tester, ident=converted_response_data["id"])
        form, converted_response_data = new_time_limited_task_helper(self, tester)
        form = time_limited_task_form_helper(self, 1, form, tester)

        response = tester.post(f"index/{tomorrow}", follow_redirects=True)

        self.assertIn(
            b"this is an edited single event of a time limited freq task", response.data
        )

    def test_time_limited_frequency_task_completion_all(self):
        """Tests that a freq time limited task does not appear today or tomorrow ."""
        tester = self.app.test_client()
        login_helper(self, tester)
        add_and_edit_task_helper(self, 2)
        form, converted_response_data = new_task_with_form_helper(self, tester)
        form_helper(8, form, tester, ident=converted_response_data["id"])
        form, converted_response_data = new_time_limited_task_helper(self, tester)
        form = time_limited_task_form_helper(self, 2, form, tester)

        response = tester.post(f"index/{tomorrow}", follow_redirects=True)
        self.assertNotIn(
            b"this is an edited single event of a time limited freq task", response.data
        )

        response = tester.post(f"index/ph", follow_redirects=True)
        self.assertNotIn(
            b"this is an edited single event of a time limited freq task", response.data
        )


def user_creation_helper(self):
    u1 = User(username="john", email="john@example.com")
    u2 = User(username="susan", email="susan@example.com")
    db.session.add(u1)
    db.session.add(u2)
    db.session.commit()
    return u1, u2


def login_helper(self, client):
    """Helper to register and log in a user to the db."""
    u1 = User(username="dave", email="john@example.com")
    db.session.add(u1)
    u1.set_password("test")
    db.session.commit()
    form = LoginForm()
    form.username.data = "dave"
    form.password.data = "test"
    response = client.post("login_page", data=form.data, follow_redirects=True)
    return response


def contacts_helper(self):
    u1 = User.query.filter_by(username="dave").first()
    u2 = User(username="susan", email="susan@example.com")
    u3 = User(username="mark", email="mark@example.com")
    db.session.add_all([u2, u3])
    db.session.commit()
    return u1, u2, u3


def message_helper(self):
    u1 = User.query.filter_by(username="dave").first()
    u2 = User(username="susan", email="susan@example.com")
    db.session.add(u2)
    for i in range(6):
        msg2 = Message(author=u1, recipient=u2, body="sent test")
        msg = Message(author=u2, recipient=u1, body="test")
        db.session.add_all([msg, msg2])
    db.session.commit()
    db.session.flush()
    return u1, u2, msg.id


def add_and_edit_task_helper(self, freq=1):
    u1 = User.query.filter_by(username="dave").first()
    for i in range(freq):
        new_task = Post(
            body="This is a test task",
            done=False,
            start_time=0,
            end_time=1000,
            date=datetime.strptime(date, "%Y-%m-%d %H:%M:%S"),
            hour=datetime.utcnow().hour,
            user_id=u1.id,
            frequency=0,
            color="#fff",
        )
        db.session.add(new_task)
        db.session.commit()


def new_task_with_form_helper(self, tester):
    form = TaskForm()
    form.task.data = "This is a single task"
    form.start_time.data = datetime.now().strftime("%H:%M")
    form.end_time.data = datetime.now().strftime("%H:%M")
    form.date.data = date
    form.color.data = "#fff"
    form.frequency.data = 0
    form.single_event.data = None
    response = tester.post("/new_task/", data=form.data)
    converted_response_data = json.loads(response.data)
    form.ident.data = converted_response_data["id"]
    return form, converted_response_data


def new_time_limited_task_helper(self, tester):
    form = TaskForm()
    form.task.data = "This is a time limited freq task"
    form.start_time.data = datetime.now().strftime("%H:%M")
    form.end_time.data = datetime.now().strftime("%H:%M")
    form.date.data = date
    form.color.data = "#fff"
    form.frequency.data = 1
    form.single_event.data = None
    form.to_date.data = tomorrow
    response = tester.post("/new_task/", data=form.data)
    converted_response_data = json.loads(response.data)
    form.ident.data = int(converted_response_data["id"])
    return form, converted_response_data


def form_helper(line, form, tester, ident=None):
    form.task.data = "This is a new task"
    form.done.data = None
    form.frequency.data = 1
    response = tester.post("/edit_task/", data=form.data)
    if line > 1:
        form.task.data = "This is an edit of a freq task"
        form.date.data = formatted_tomorrow
        form.single_event.data = True
        form.done.data = None
        response = tester.post("/edit_task/", data=form.data)
    if line > 2:
        form.ident.data = 4
        form.single_event.data = None
        form.frequency.data = 2
        response = tester.post("/edit_task/", data=form.data)
    if line > 3:
        form.frequency.data = 1
        form.ident.data = ident
        response = tester.post("/edit_task/", data=form.data)
    if line > 4:
        form.ident.data = 4
        form.task.data = "Edit on all related tasks from a child task"
        response = tester.post("/edit_task/", data=form.data)
    if line > 5:
        form.single_event.data = True
        form.task.data = "This is an edit of the original freq task"
        form.date.data = date
        response = tester.post("/edit_task/", data=form.data)
    if line > 6:
        form.ident.data = 4
        form.date.data = formatted_tomorrow
        form.done.data = True
        response = tester.post("/edit_task/", data=form.data)
    if line > 7:
        form.ident.data = ident
        form.done.data = True
        form.single_event.data = None
        response = tester.post("/edit_task/", data=form.data)
    return form


def time_limited_task_form_helper(self, line, form, tester):
    if line > 0:
        form.done.data = None
        form.date.data = formatted_tomorrow
        form.single_event.data = True
        form.task.data = "this is an edited single event of a time limited freq task"
        response = tester.post("/edit_task/", data=form.data)
    if line > 1:
        form.single_event.data = None
        form.date.data = date
        form.done.data = True
        response = tester.post("/edit_task/", data=form.data)
    return form


date = datetime.strftime(datetime.utcnow().date(), "%Y-%m-%d %H:%M:%S")
tomorrow = datetime.strftime(datetime.utcnow().date() + timedelta(days=1), "%d-%m-%Y")
yesterday = datetime.strftime(datetime.utcnow().date() - timedelta(days=1), "%d-%m-%Y")
formatted_tomorrow = datetime.strftime(
    datetime.utcnow().date() + timedelta(days=1), "%Y-%m-%d %H:%M:%S"
)

if __name__ == "__main__":
    unittest.main(verbosity=2)
