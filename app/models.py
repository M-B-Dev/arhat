from datetime import datetime

from time import time

import jwt

from werkzeug.security import generate_password_hash, check_password_hash

from flask_login import UserMixin

from flask import current_app

from app import db, login


followers = db.Table('followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

penders = db.Table('penders',
    db.Column('pender_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('pendered_id', db.Integer, db.ForeignKey('user.id'))
)


class User(UserMixin, db.Model):
    """User class. The schema for the database user table.
    
    password_hash: hashed password
    posts: These are the user tasks
    last_seen: The date and time the user last logged in TODO delete
    subscription: The notificaiton subscription dictionary
    subscribed: local record of whether a user wants notifications or not
    sent_date: The date that depression notifcations were last sent
    threshold: The percentage of incomplete tasks that will 
        trigger messages to be sent to followers
    days: The number of previous days that will be checked for 
        incomplete tasks
    followed: Other users that are followed by user
    pended: Users who have not confirmed follow request
    last_message_read_time: The last time a message was read by the user  
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=False)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    image_file = db.Column(
        db.String(20), 
        nullable=True, 
        default='default.jpg'
        )
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    subscription = db.Column(db.String(1000), nullable=True)
    subscribed = db.Column(db.Boolean, default=False)
    sent_date = db.Column(db.String(120), nullable=True)
    threshold = db.Column(db.Integer, nullable=True)
    days = db.Column(db.Integer, nullable=True)
    followed = db.relationship(
        'User', secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref('followers', lazy='dynamic'), lazy='dynamic')
    pended = db.relationship(
        'User', secondary=penders,
        primaryjoin=(penders.c.pender_id == id),
        secondaryjoin=(penders.c.pendered_id == id),
        backref=db.backref('penders', lazy='dynamic'), lazy='dynamic')

    def __repr__(self):
        """returns a formatted user object."""
        return '<User {}>'.format(self.username)

    def set_password(self, password):
        """Returns a hashed password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks that the password hash matches that db hash."""
        return check_password_hash(self.password_hash, password)

    def pend(self, user):
        """appends a user to the pended table before 
        follow request has been accepted.

        """

        if not self.is_pending(user):
            self.pended.append(user)

    def unpend(self, user):
        """Removes a user from the pended table once follow request
        has been accepted.

        """

        if self.is_pending(user):
            self.pended.remove(user)

    def is_pending(self, user):
        """Returns the number of users pending follow requests."""
        return self.pended.filter(
            penders.c.pendered_id == user.id).count() > 0

    def follow(self, user):
        """Returns the number of users that are following current user."""
        if not self.is_following(user):
            self.followed.append(user)

    def unfollow(self, user):
        """Allows a user to unfollow another."""
        if self.is_following(user):
            self.followed.remove(user)

    def is_following(self, user):
        """Returns the number of users current user is following."""
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def get_reset_password_token(self, expires_in=600):
        """returns a reset password token."""
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            current_app.config['SECRET_KEY'], 
            algorithm='HS256'
            ).decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        """Checks validity of reset password token."""
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)

    def get_follow_request_token(self):
        """returns a follow request token."""
        return jwt.encode(
            {'follow_request': self.id},
            current_app.config['SECRET_KEY'], 
            algorithm='HS256'
            ).decode('utf-8')

    @staticmethod
    def verify_follow_request_token(token):
        """Checks the validity of the follow request token."""
        try:
            id = jwt.decode(token, current_app.config['SECRET_KEY'],
                            algorithms=['HS256'])['follow_request']
        except:
            return
        return User.query.get(id)



    messages_sent = db.relationship('Message',
                                    foreign_keys='Message.sender_id',
                                    backref='author', lazy='dynamic')
    
    messages_received = db.relationship('Message',
                                        foreign_keys='Message.recipient_id',
                                        backref='recipient', lazy='dynamic')
    
    last_message_read_time = db.Column(db.DateTime)
        
    def new_messages(self):
        """returns the time that current user read a message."""
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return Message.query.filter_by(recipient=self).filter(
            Message.timestamp > last_read_time).count()
            
@login.user_loader
def load_user(id):
    """helper function to load user."""
    return User.query.get(int(id))


class Post(db.Model):
    """db schema model for to do tasks.
    
    body: Main text of the tasks. 
    timestamp: when the task was created.
    hour: The hour that the task is due.
    depression_score: TODO needs removal.
    done: Whether the task has been completed or not.
    """

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140), default="")
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    hour = db.Column(db.Integer)
    done = db.Column(db.Boolean, default=False)
    depression_score = db.Column(db.Integer, default=0)
    date = db.Column(db.DateTime, index=True, default=datetime.today())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    start_time = db.Column(db.Integer, nullable=True)
    end_time = db.Column(db.Integer, nullable=True)
    frequency = db.Column(db.Integer, nullable=True)
    color = db.Column(db.String(14), nullable=True, default="6c757d")
    exclude = db.Column(db.Integer, nullable=True)


    def __repr__(self):
        """returns a representation of the Post object."""
        return '<Post {}>'.format(self.body)

class Message(db.Model):
    """db schema for private messages sent by the users."""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        """returns a representation of the Message object."""
        return '<Message {}>'.format(self.body)