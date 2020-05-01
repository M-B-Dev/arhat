from datetime import datetime, timedelta

import unittest

from app.models import User, Post, Message

from app import create_app, db

from config import Config


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'


class UserModelCase(unittest.TestCase):
    """Test suite."""

    def setUp(self):
        """Initializes database."""
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
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

        msg = Message(author=u1,
                    recipient=u2,
                    body=""
                    )
        db.session.add(msg)
        db.session.commit()

        self.assertEqual(u1.messages_sent.count(), 1)
        self.assertEqual(u2.messages_received.count(), 1)

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
        self.assertEqual(len(people), 1)

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

        token = u1.get_reset_password_token()
        self.assertIsNotNone(u1.verify_reset_password_token(token))




if __name__ == '__main__':
    unittest.main(verbosity=2)