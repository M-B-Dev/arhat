import os
import secrets
import base64
from datetime import datetime, timedelta
from time import time

import jwt
from flask import current_app, flash, url_for
from flask_login import UserMixin, current_user
from PIL import Image
from werkzeug.security import check_password_hash, generate_password_hash

from app import db, login
from app.email import send_email

followers = db.Table(
    "followers",
    db.Column("follower_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("followed_id", db.Integer, db.ForeignKey("user.id")),
)

penders = db.Table(
    "penders",
    db.Column("pender_id", db.Integer, db.ForeignKey("user.id")),
    db.Column("pendered_id", db.Integer, db.ForeignKey("user.id")),
)


class PaginatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        if page is not None:
            resources = query.paginate(page, per_page, False)
            data = {
                    'items': [item.to_dict() for item in resources.items],
                    '_meta': {
                        'page': page,
                        'per_page': per_page,
                        'total_pages': resources.pages,
                        'total_items': resources.total
                    },
                    '_links': {
                        'self': url_for(endpoint, page=page, per_page=per_page,
                                        **kwargs),
                        'next': url_for(endpoint, page=page + 1, per_page=per_page,
                                        **kwargs) if resources.has_next else None,
                        'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                                        **kwargs) if resources.has_prev else None
                    }
                }      
        else:
            data = {
                'items': [item.to_dict() for item in query]
            }
        return data


class User(PaginatedAPIMixin, UserMixin, db.Model):
    """
    User class. The schema for the database user table.
    
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
    image_file = db.Column(db.String(20), nullable=True, default="default.jpg")
    posts = db.relationship("Post", backref="author", lazy="dynamic")
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    subscription = db.Column(db.String(1000), nullable=True)
    subscribed = db.Column(db.Boolean, default=False)
    sent_date = db.Column(db.String(120), nullable=True)
    threshold = db.Column(db.Integer, nullable=True)
    days = db.Column(db.Integer, nullable=True)
    followed = db.relationship(
        "User",
        secondary=followers,
        primaryjoin=(followers.c.follower_id == id),
        secondaryjoin=(followers.c.followed_id == id),
        backref=db.backref("followers", lazy="dynamic"),
        lazy="dynamic",
    )
    pended = db.relationship(
        "User",
        secondary=penders,
        primaryjoin=(penders.c.pender_id == id),
        secondaryjoin=(penders.c.pendered_id == id),
        backref=db.backref("penders", lazy="dynamic"),
        lazy="dynamic",
    )
    token = db.Column(db.String(32), index=True, unique=True)
    token_expiration = db.Column(db.DateTime)

    def __repr__(self):
        """returns a formatted user object."""
        return "<User {}>".format(self.username)

    def set_password(self, password):
        """Returns a hashed password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks that the password hash matches that db hash."""
        return check_password_hash(self.password_hash, password)

    def pend(self, user):
        """
        appends a user to the pended table before 
        follow request has been accepted.

        """

        if not self.is_pending(user):
            self.pended.append(user)

    def unpend(self, user):
        """
        Removes a user from the pended table once follow request
        has been accepted.

        """

        if self.is_pending(user):
            self.pended.remove(user)

    def is_pending(self, user):
        """Returns the number of users pending follow requests."""
        return self.pended.filter(penders.c.pendered_id == user.id).count() > 0

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
        return self.followed.filter(followers.c.followed_id == user.id).count() > 0

    def get_reset_password_token(self, expires_in=600):
        """returns a reset password token."""
        return jwt.encode(
            {"reset_password": self.id, "exp": time() + expires_in},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        ).decode("utf-8")

    @staticmethod
    def verify_reset_password_token(token):
        """Checks validity of reset password token."""
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["reset_password"]
        except:
            return
        return User.query.get(id)

    def get_follow_request_token(self):
        """returns a follow request token."""
        return jwt.encode(
            {"follow_request": self.id},
            current_app.config["SECRET_KEY"],
            algorithm="HS256",
        ).decode("utf-8")

    @staticmethod
    def verify_follow_request_token(token):
        """Checks the validity of the follow request token."""
        try:
            id = jwt.decode(
                token, current_app.config["SECRET_KEY"], algorithms=["HS256"]
            )["follow_request"]
        except:
            return
        return User.query.get(id)

    messages_sent = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="author", lazy="dynamic"
    )

    messages_received = db.relationship(
        "Message",
        foreign_keys="Message.recipient_id",
        backref="recipient",
        lazy="dynamic",
    )

    last_message_read_time = db.Column(db.DateTime)

    def new_messages(self):
        """returns the time that current user read a message."""
        last_read_time = self.last_message_read_time or datetime(1900, 1, 1)
        return (
            Message.query.filter_by(recipient=self)
            .filter(Message.timestamp > last_read_time)
            .count()
        )

    def save_picture(self, form_picture):
        """
        This reformats an image into manageable a size and with dimensions.
        
        Also, this will delete any previous profile image from the db.
        """
        if current_user.image_file and current_user.image_file != "default.jpg":
            os.remove(
                current_app.root_path
                + "//static/profile_pics//"
                + current_user.image_file
            )
        random_hex = secrets.token_hex(8)
        _, f_ext = os.path.splitext(form_picture.filename)
        picture_fn = random_hex + f_ext
        picture_path = os.path.join(
            current_app.root_path, "static/profile_pics", picture_fn
        )
        output_size = (250, 250)
        i = Image.open(form_picture)
        i.thumbnail(output_size)
        i.save(picture_path)
        self.image_file = picture_fn

    def check_freq_tasks_in_days(self):
        """
        Finds all frequency tasks that occur in 
        the user set depression check day range.
        
        """
        for self.freq_task in self.outstanding_frequency_tasks:
            if (
                self.freq_task.frequency != 0
                and (
                    self.date_for_depress_check(self.date_set) - self.freq_task.date
                ).days
                > 0
                and (
                    self.date_for_depress_check(self.date_set) - self.freq_task.date
                ).days
                % self.freq_task.frequency
                == 0
            ):
                self.freq_daily_tasks += 1
                self.check_for_edited_freqs()

    def check_for_edited_freqs(self):
        """
        Removes any edited frequency tasks from the depression check
        (These will be picked up by subsequent check of all individual tasks)
        """
        for self.tsk in self.daily_tasks:
            if self.tsk.exclude == self.freq_task.id:
                self.freq_daily_tasks -= 1

    def check_tasks_in_days(self):
        """
        Sets up for loop and variables for checking through tasks
        that occured during depression check day range.

        """
        for self.day in range(self.days):
            self.date_set = self.date_set - timedelta(days=1)
            self.daily_tasks = self.posts.filter_by(
                date=self.date_for_depress_check(self.date_set)
            )
            self.done_tasks = 0
            self.freq_daily_tasks = 0
            self.freq_done_tasks = 0
            self.check_freq_tasks_in_days()
            self.check_tasks_over_0()

    def check_if_task_done(self):
        """Checks if task is done and totals these."""
        for self.task in self.daily_tasks:
            if self.task.done == True:
                self.done_tasks += 1

    def check_tasks_over_0(self):
        """
        If tasks occured on the day in question
        calculates daily depression percentage 
        (done tasks divided by tasks due)
        Adds this value to a running total and increments 
        the number of days to divide by.

        """
        if self.daily_tasks.count() > 0:
            self.check_if_task_done()
            self.daily_percentage = (
                self.done_tasks / self.daily_tasks.count() + self.freq_daily_tasks
            ) * 100
            self.divide_days += 1
            self.period_precentage += self.daily_percentage
        elif self.freq_daily_tasks > 0:
            self.divide_days += 1

    def check_divide_days_over_0(self):
        """
        Checks that divide days is over 0,
        anything under signifies that no tasks 
        were set during the depression check date range.

        """
        if self.divide_days > 0:
            self.period_precentage /= self.divide_days
        else:
            self.period_precentage = 100

    def check_depression(self):
        """
        Checks if the percentage of complete tasks is lower than 
        the user set threshold. If lower then then messages and emails
        are sent to all users that the current user follows. 
        
        """
        self.all_frequency_tasks = self.posts.filter(Post.frequency != None).all()
        self.outstanding_frequency_tasks = [
            task for task in self.all_frequency_tasks if task.done is False
        ]
        self.date_set = datetime.utcnow().date()
        self.daily_percentage = 0
        self.period_precentage = 0
        self.divide_days = 0
        self.check_tasks_in_days()
        self.check_divide_days_over_0()
        self.check_percentage_against_threshold()

    def check_percentage_against_threshold(self):
        """
        Checks that depression percentage is below the user set threshold. 
        If so, emails will be sent to followers.
        """
        if self.period_precentage < self.threshold:
            for followed in self.followed.all():
                send_email(
                    "Urgent",
                    current_app.config["ADMINS"][0],
                    [followed.email],
                    f"please contact {self.username}",
                    html_body=None,
                )
                msg = Message(
                    author=self,
                    recipient=followed,
                    body=f"please contact {self.username}",
                )
                db.session.add(msg)
                db.session.commit()

    def date_for_depress_check(self, date_set):
        """Formats short date for depression check, from string, to datetime."""
        return datetime.strptime(str(date_set), "%Y-%m-%d")

    def add_sent_date_check_depression(self, date):
        """Triggers depression check and sets depression check date."""
        self.check_depression()
        self.sent_date = date
        db.session.commit()

    def check_if_depression_sent(self, date):
        """
        Checks that depression check has not already occured today.
        and that a threshold and date range has been set by the user.

        """
        today = datetime.strftime(datetime.utcnow().date(), "%Y-%m-%d %H:%M:%S")
        if self.sent_date:
            if str(self.sent_date) != today:
                self.add_sent_date_check_depression(date)
        elif self.threshold and self.days:
            self.add_sent_date_check_depression(today)

    def to_dict(self, include_email=False):
        data = {
            'id': self.id,
            'username': self.username,
            'last_seen': self.last_seen.isoformat() + 'Z',
            'post_count': self.posts.count(),
            'follower_count': self.followers.count(),
            'followed_count': self.followed.count(),
            '_links': {
                'self': url_for('api.get_user', id=self.id),
                'followers': url_for('api.get_followers', id=self.id),
                'followed': url_for('api.get_followed', id=self.id)
            }
        }
        if include_email:
            data['email'] = self.email
        return data

    def from_dict(self, data, new_user=False):
        for field in ['username', 'email', 'threshold', 'days']:
            if field in data:
                setattr(self, field, data[field])
        if new_user and 'password' in data:
            self.set_password(data['password'])

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.token and self.token_expiration > now + timedelta(seconds=60):
            return self.token
        self.token = base64.b64encode(os.urandom(24)).decode('utf-8')
        self.token_expiration = now + timedelta(seconds=expires_in)
        db.session.add(self)
        return self.token

    def revoke_token(self):
        self.token_expiration = datetime.utcnow() - timedelta(seconds=1)

    @staticmethod
    def check_token(token):
        user = User.query.filter_by(token=token).first()
        if user is None or user.token_expiration < datetime.utcnow():
            return None
        return user

    def get_daily_tasks(self, date):
        date = datetime.strptime(date, "%d-%m-%Y")
        all_frequency_tasks = self.posts.filter(Post.frequency != None).all()
        todos = self.posts.filter_by(date=date)
        exclusions = [todo.exclude for todo in todos if todo.exclude]
        all_tasks = [
            task
            for task in all_frequency_tasks
            if task.frequency > 0
            and (date - task.date).days > 0
            and ((date - task.date).days % task.frequency) == 0
            and task.date < date
            and task.id not in exclusions
            and task not in todos
        ]
        [all_tasks.append(task) for task in todos if task.done is False]
        return all_tasks


@login.user_loader
def load_user(id):
    """helper function to load user."""
    return User.query.get(int(id))


class Post(db.Model):
    """
    db schema model for to do tasks.
    
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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    start_time = db.Column(db.Integer, nullable=True)
    end_time = db.Column(db.Integer, nullable=True)
    frequency = db.Column(db.Integer, nullable=True)
    color = db.Column(db.String(14), nullable=True, default="6c757d")
    exclude = db.Column(db.Integer, nullable=True)
    to_date = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        data = {
            'id': self.id,
            'body': self.body,
            'start_time': self.start_time,
            'end_time': self.end_time,
            'color': self.color,
            'frequency': self.frequency,
            'to_date': self.to_date,
            'done': self.done
        }
        return data

    def from_dict(self, data):
        if 'date' in data:
            data['date'] = datetime.strptime(data['date'], "%d-%m-%Y")
            data['user_id'] = int(data['user_id'])
            data['hour'] = 1
        if data['frequency']:
            data['frequency'] = int(data['frequency'])
        if 'done' in data:
                print(data['done'])
        if 'done' in data and data['done'] == 'True':
            data['done'] = True
            data['frequency'] = None
        elif 'done' in data and data['done'] == 'False':
            data['done'] = False
        for field in ['body', 'done', 'start_time', 'end_time', 'user_id', 'date', 'hour', 'frequency', 'to_date']:
            if field in data:
                setattr(self, field, data[field])

    def __repr__(self):
        """returns a representation of the Post object."""
        return "<Post {}>".format(self.body)

    def calc_mins_height_and_end(self):
        """Calculates the start (minutes), length (height) and end of a task."""
        self.minutes = (
            self.form.start_time.data.hour * 60
        ) + self.form.start_time.data.minute
        self.height = (
            (self.form.end_time.data.hour * 60) + self.form.end_time.data.minute
        ) - self.minutes
        self.end = (self.form.end_time.data.hour * 60) + self.form.end_time.data.minute

    def set_frequency(self):
        """Sets an inputted frequency of 0 to a NoneType."""
        if self.form.frequency.data == 0:
            self.form.frequency.data = None

    def add_multiple_tasks(self):
        """Adds multiple tasks, triggered when a repeating task has a date_to value."""
        for self.i in range((self.to_date - self.date).days, -1, -1):
            self.task_to_be_added = self.add_single_task(to_date=self.to_date)
            db.session.add(self.task_to_be_added)
            self.commit_flush()
            if self.i == (self.to_date - self.date).days:
                self.ident = self.task_to_be_added.id
            self.task_to_be_added.exclude = self.ident
            db.session.commit()

    def add_single_task(self, date=None, frequency=None, to_date=None):
        """Adds a single task."""
        if date is None:
            date = self.date + timedelta(days=self.i)
        return Post(
            date=date,
            body=self.form.task.data,
            hour=self.form.start_time.data.hour,
            done=False,
            user_id=current_user.id,
            start_time=self.minutes,
            end_time=self.end,
            color=self.form.color.data,
            frequency=frequency,
            to_date=to_date,
        )

    def commit_flush(self):
        """Commits to db then flushes, in order to get id of commited task."""
        db.session.commit()
        db.session.flush()

    def string_to_datetime(self, date):
        """converts date string to specific format."""
        return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    def edit_single_freq_task(self):
        """Edits a frequency task (by creating a new, related task in its place)."""
        self.task_to_be_added = self.add_single_task(
            date=self.string_to_datetime(self.form.date.data)
        )
        self.task_to_be_added.exclude = int(self.form.ident.data)
        self.task_to_be_edited.exclude = self.task_to_be_edited.id

        if self.string_to_datetime(self.form.date.data) == self.task_to_be_edited.date:
            self.task_to_be_edited.done = True
        db.session.add(self.task_to_be_added)
        if self.task_to_be_added.done is False:
            flash("Your single task has been updated!", "success")
        else:
            flash("Your single task is complete!", "success")

    def edit_single_task(self):
        """
        Edits a single, previously edited frequency task, 
        or individual, repeating task with to_date.

        """
        if self.task_to_be_edited.exclude and self.task_to_be_edited.exclude != int(
            self.form.ident.data
        ):
            self.task_to_be_edited_input()
            self.task_to_be_edited.frequency = 0
            if self.task_to_be_edited.done is False:
                flash("Your single task has been updated!", "success")
            else:
                flash("Your single task is complete!", "success")

    def task_to_be_edited_input(self):
        """sets task to be edited values from form."""
        self.task_to_be_edited.body = self.form.task.data
        self.task_to_be_edited.hour = self.form.start_time.data.hour
        self.task_to_be_edited.done = self.form.done.data
        self.task_to_be_edited.user_id = current_user.id
        self.task_to_be_edited.start_time = self.minutes
        self.task_to_be_edited.end_time = self.end
        self.task_to_be_edited.color = self.form.color.data

    def edit_all_freq_parent_and_child_tasks(self):
        """
        Edits all repeating/frequency tasks, 
        inlcuding any child or parent tasks.
        
        """
        self.parent_task = current_user.posts.filter_by(
            id=self.task_to_be_edited.exclude
        ).first()
        if not self.parent_task.to_date:
            self.parent_task.frequency = self.form.frequency.data
        self.tasks = [
            task
            for task in current_user.posts.all()
            if task.exclude == self.task_to_be_edited.exclude
        ]
        for i, task in enumerate(self.tasks):
            task.body = self.form.task.data
            task.hour = self.form.start_time.data.hour
            task.done = self.form.done.data
            if self.form.done.data is True:
                task.frequency = 0
            elif self.form.frequency.data != None and self.form.frequency.data == 0:
                if i != len(self.tasks) - 1:
                    task.done = True
            elif (
                self.form.frequency.data
                and (
                    (self.parent_task.date - task.date).days
                    % int(self.form.frequency.data)
                )
                != 0
            ):
                task.done = True
            task.color = self.form.color.data
            task.user_id = current_user.id
            task.start_time = self.minutes
            task.end_time = self.end
        flash("Your tasks have been updated!", "success")

    def edit_all_tasks(self):
        """Edits all tasks in a series."""
        self.task_to_be_edited_input()
        self.task_to_be_edited.date = self.string_to_datetime(self.form.date.data)
        if self.task_to_be_edited.done == True:
            self.task_to_be_edited.frequency = 0
        else:
            self.task_to_be_edited.frequency = self.form.frequency.data
        if self.task_to_be_edited.done is False:
            flash("Your task has been updated!", "success")
        else:
            flash("Your task is complete!", "success")


class Message(db.Model):
    """db schema for private messages sent by the users."""

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)

    def __repr__(self):
        """returns a representation of the Message object."""
        return "<Message {}>".format(self.body)


