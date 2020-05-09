import json
from datetime import date, datetime, timedelta

from flask import (
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import current_user, login_required
from pywebpush import webpush

from app import db
from app.email import send_email
from app.main import bp
from app.main.forms import DateForm, TaskForm
from app.models import Message, Post, User


@bp.route("/index/<date_set>", methods=["GET", "POST"])
@login_required
def index(date_set):
    """Render the index page.

    date_set: argument that is used to retreive tasks for 
    a specific date or, if set to 'ph', will default to today's date.

    """
    date_form = DateForm()

    if date_form.validate_on_submit():
        return redirect(
            url_for(
                "main.index", date_set=datetime_to_string(date_form.datepicker.data)
            )
        )
    form = TaskForm()
    date_form = DateForm()
    date = set_date(date_set)
    today = False
    if convert_date_format(datetime.utcnow()) == date:
        today = True
    check_if_depression_sent(date)
    date_form.datepicker.data = date
    all_frequency_tasks = current_user.posts.filter(Post.frequency != None).all()
    todos = current_user.posts.filter_by(date=date)
    exclusions = [todo.exclude for todo in todos if todo.exclude]
    frequency_tasks = [
        task
        for task in all_frequency_tasks
        if task.frequency > 0
        and (date - task.date).days > 0
        and ((date - task.date).days % task.frequency) == 0
        and task.date < date
        and task.id not in exclusions
    ]
    return render_template(
        "index.html",
        frequency_tasks=frequency_tasks,
        today=today,
        todos=todos,
        date_set=date_set,
        title="Home Page",
        form=form,
        date_form=date_form,
    )


class NewTask:
    def __init__(self):
        self.form = TaskForm()

    def calc_mins_height_and_end(self):
        self.minutes = (
            self.form.start_time.data.hour * 60
        ) + self.form.start_time.data.minute
        self.height = (
            (self.form.end_time.data.hour * 60) + self.form.end_time.data.minute
        ) - self.minutes
        self.end = (self.form.end_time.data.hour * 60) + self.form.end_time.data.minute

    def set_frequency(self):
        if self.form.frequency.data == 0:
            self.form.frequency.data = None

    def add_multiple_tasks(self):
        for self.i in range((self.to_date - self.date).days, -1, -1):
            self.task_to_be_added = self.add_single_task()
            db.session.add(self.task_to_be_added)
            commit_flush()
            if self.i == (self.to_date - self.date).days:
                self.ident = self.task_to_be_added.id
            self.task_to_be_added.exclude = self.ident
            db.session.commit()

    def add_single_task(self, date=None, frequency=0):
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
        )


@bp.route("/new_task/", methods=["GET", "POST"])
@login_required
def new_task():
    """Creates a new todo task."""
    new_task = NewTask()
    if not new_task.form.validate_on_submit():
        return redirect(url_for("main.index", date_set="ph"))
    else:
        new_task.calc_mins_height_and_end()
        if new_task.minutes > new_task.end:
            return redirect(url_for("main.index", date_set="ph"))
        new_task.set_frequency()
        if new_task.form.frequency.data and new_task.form.to_date.data:
            new_task.to_date = convert_date_format(new_task.form.to_date.data)
            new_task.date = string_to_datetime(new_task.form.date.data)
            if new_task.to_date > new_task.date:
                new_task.add_multiple_tasks()
                flash("Your tasks are now live!", "success")
            else:
                return redirect(url_for("main.index", date_set="ph"))
        elif not new_task.form.to_date.data:
            task_to_be_added = new_task.add_single_task(
                date=string_to_datetime(new_task.form.date.data),
                frequency=new_task.form.frequency.data,
            )
            db.session.add(task_to_be_added)
            commit_flush()
            new_task.ident = task_to_be_added.id
            flash("Your task is now live!", "success")
        else:
            return redirect(url_for("main.index", date_set="ph"))
        return jsonify(
            {
                "minutes": new_task.minutes,
                "height": new_task.height,
                "task": new_task.form.task.data,
                "id": new_task.ident,
                "color": new_task.form.color.data,
                "frequency": new_task.form.frequency.data,
            }
        )


@bp.route("/edit_task/", methods=["GET", "POST"])
@login_required
def edit_task():
    form = TaskForm()
    if not form.validate_on_submit():
        return redirect(url_for("main.index", date_set="ph"))
    else:
        task_to_be_edited = current_user.posts.filter_by(
            id=int(form.ident.data)
        ).first()
        minutes, _, end = calc_mins_height_and_end(form)
        if form.single_event.data is True:
            if task_to_be_edited.exclude and task_to_be_edited.exclude != int(
                form.ident.data
            ):
                edit_single_task(task_to_be_edited, form, minutes, end)
            else:
                edit_single_freq_task(minutes, form, end, task_to_be_edited)
        else:
            if task_to_be_edited.exclude:
                edit_all_freq_parent_and_child_tasks(
                    task_to_be_edited, form, minutes, end
                )
            else:
                edit_all_tasks(task_to_be_edited, minutes, end, form)
        db.session.commit()
        return jsonify({"id": form.ident.data})


@bp.route("/update_task/", methods=["GET", "POST"])
@login_required
def update_task():
    if request.method == "POST":
        data = request.get_json()
        task = Post.query.filter_by(id=int(data["id"])).first()
        height = "".join([n for n in data["height"] if n.isnumeric()])
        top = "".join([n for n in data["top"] if n.isnumeric()])
        task.start_time = int(top)
        task.end_time = int(height) + int(top)
        db.session.commit()
    return jsonify({"task": task.body})


@bp.route("/", methods=["GET", "POST"])
def home():
    """This reroutes to index with the date_set argument."""
    return redirect(url_for("main.index", date_set="ph"))


@bp.route("/check", methods=["GET", "POST"])
@login_required
def check():
    """Checks if any tasks are due. 
    
    If tasks are due a notification is triggered. 
    """

    if current_user.subscribed and str(request.args.get("id")).isnumeric():
        ident = int(request.args.get("id"))
        task = current_user.posts.filter_by(id=ident).first()
        send_web_push(
            json.loads(User.query.all()[0].subscription), f"You need to {task.body}"
        )
    else:
        ident = False
    return jsonify({"id": ident})


@bp.route("/complete", methods=["GET", "POST"])
@login_required
def complete():
    """Clears completed tasks from the database and reloads index"""
    if request.args:
        if request.args.get("id").isnumeric():
            ident = int(request.args.get("id"))
            task = current_user.posts.filter_by(id=ident)
            task[0].done = True
            db.session.commit()
    return redirect(url_for("main.index", date_set="ph"))


def check_depression(user=current_user, app=current_app):
    """Checks if the percentage of complete tasks is lower than 
    the user set threshold. If lower then then messages and emails
    are sent to all users that the current user follows. 
    
    """
    all_frequency_tasks = user.posts.filter(Post.frequency != None).all()
    outstanding_frequency_tasks = [
        task for task in all_frequency_tasks if task.done is False
    ]
    threshold = user.threshold
    date_set = datetime.utcnow().date()
    daily_percentage = 0
    number_of_days = user.days
    period_precentage = 0
    divide_days = 0
    for day in range(number_of_days):
        date_set = date_set - timedelta(days=1)
        daily_tasks = user.posts.filter_by(date=date_for_despress_check(date_set))
        done_tasks = 0
        freq_daily_tasks = 0
        freq_done_tasks = 0
        for freq_task in outstanding_frequency_tasks:
            if (
                freq_task.frequency != 0
                and (date_for_despress_check(date_set) - freq_task.date).days > 0
                and (date_for_despress_check(date_set) - freq_task.date).days
                % freq_task.frequency
                == 0
            ):
                freq_daily_tasks += 1
                for tsk in daily_tasks:
                    if tsk.exclude == freq_task.id:
                        freq_daily_tasks -= 1
        if daily_tasks.count() > 0:
            for task in daily_tasks:
                if task.done == True:
                    done_tasks += 1
            daily_percentage = (
                done_tasks / daily_tasks.count() + freq_daily_tasks
            ) * 100
            divide_days += 1
            period_precentage += daily_percentage
        elif freq_daily_tasks > 0:
            divide_days += 1
    if divide_days > 0:
        period_precentage /= divide_days
    else:
        period_precentage = 100
    if period_precentage < threshold:
        for followed in user.followed.all():
            send_email(
                "Urgent",
                app.config["ADMINS"][0],
                [followed.email],
                f"please contact {user.username}",
                html_body=None,
            )
            msg = Message(
                author=user, recipient=followed, body=f"please contact {user.username}"
            )
            db.session.add(msg)
            db.session.commit()
    return redirect(url_for("main.index", date_set="ph"))


@bp.route("/subscribe/", methods=["GET", "POST"])
def subscribe():
    """Gets and stores a user notification subscription in the db."""
    subscription = request.json.get("sub_token")
    User.query.all()[0].subscription = json.dumps(subscription)
    db.session.commit()
    return redirect(url_for("sn.edit_profile"))


@bp.route("/subscription/", methods=["GET", "POST"])
def subscription():
    """POST creates a subscription.

    GET returns vapid public key which clients uses 
    to send around push notification.
    """

    if request.method == "GET":
        return Response(
            response=json.dumps({"public_key": current_app.config["VAPID_PUBLIC_KEY"]}),
            headers={"Access-Control-Allow-Origin": "*"},
            content_type="application/json",
        )
    subscription_token = request.get_json("subscription_token")
    return Response(status=201, mimetype="application/json")


@bp.route("/unsubscribe", methods=["GET", "POST"])
def unsubscribe():
    """turns off user notifications."""
    current_user.subscribed = False
    current_user.subscription = None
    db.session.commit()
    return redirect(url_for("main.index", date_set="ph"))


@bp.route("/sub", methods=["GET", "POST"])
def flask_subscribe():
    """Sets user notifications to off in the database."""
    if not current_user.subscribed:
        current_user.subscribed = True
    else:
        current_user.subscribed = False
    db.session.commit()
    return redirect(url_for("sn.edit_profile"))


def add_sent_date_check_depression(date, user=current_user):
    check_depression()
    user.sent_date = date
    db.session.commit()


def check_if_depression_sent(date, user=current_user):
    today = datetime.strftime(datetime.utcnow().date(), "%Y-%m-%d %H:%M:%S")
    if user.sent_date:
        if str(user.sent_date) != today:
            add_sent_date_check_depression(date)
    elif user.threshold and user.days:
        add_sent_date_check_depression(today)


def set_date(date_set):
    if date_set == "ph":
        return convert_date_format(datetime.utcnow())
    else:
        return datetime.strptime(date_set, "%d-%m-%Y")


def send_web_push(subscription_information, message_body):
    """Triggers notifications by initializing JS Service Worker"""
    return webpush(
        subscription_info=subscription_information,
        data=message_body,
        vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
        vapid_claims=current_app.config["VAPID_CLAIMS"],
    )


def task_to_be_edited_input(task_to_be_edited, minutes, end, form):
    task_to_be_edited.body = form.task.data
    task_to_be_edited.hour = form.start_time.data.hour
    task_to_be_edited.done = form.done.data
    task_to_be_edited.user_id = current_user.id
    task_to_be_edited.start_time = minutes
    task_to_be_edited.end_time = end
    task_to_be_edited.color = form.color.data
    return task_to_be_edited


def edit_single_task(task_to_be_edited, form, minutes, end):
    if task_to_be_edited.exclude and task_to_be_edited.exclude != int(form.ident.data):
        task_to_be_edited = task_to_be_edited_input(
            task_to_be_edited, minutes, end, form
        )
        task_to_be_edited.frequency = 0
        if task_to_be_edited.done is False:
            flash("Your single task has been updated!", "success")
        else:
            flash("Your single task is complete!", "success")


def edit_single_freq_task(minutes, form, end, task_to_be_edited):
    task_to_be_added = add_single_task(
        0, minutes, form, end, string_to_datetime(form.date.data), done=form.done.data
    )
    task_to_be_added.exclude = int(form.ident.data)
    task_to_be_edited.exclude = task_to_be_edited.id
    if string_to_datetime(form.date.data) == task_to_be_edited.date:
        task_to_be_edited.done = True
    db.session.add(task_to_be_added)
    if task_to_be_added.done is False:
        flash("Your single task has been updated!", "success")
    else:
        flash("Your single task is complete!", "success")


def edit_all_freq_parent_and_child_tasks(task_to_be_edited, form, minutes, end):
    parent_task = current_user.posts.filter_by(id=task_to_be_edited.exclude).first()
    parent_task.frequency = form.frequency.data
    tasks = [
        task
        for task in current_user.posts.all()
        if task.exclude == task_to_be_edited.exclude
    ]
    for task in tasks:
        task.body = form.task.data
        task.hour = form.start_time.data.hour
        task.done = form.done.data
        if form.done.data is True:
            task.frequency = 0
        elif ((parent_task.date - task.date).days % int(form.frequency.data)) != 0:
            task.done = True
        task.color = form.color.data
        task.user_id = current_user.id
        task.start_time = minutes
        task.end_time = end
    flash("Your tasks have been updated!", "success")


def edit_all_tasks(task_to_be_edited, minutes, end, form):
    task_to_be_edited = task_to_be_edited_input(task_to_be_edited, minutes, end, form)
    task_to_be_edited.date = string_to_datetime(form.date.data)
    if task_to_be_edited.done == True:
        task_to_be_edited.frequency = 0
    else:
        task_to_be_edited.frequency = form.frequency.data
    if task_to_be_edited.done is False:
        flash("Your task has been updated!", "success")
    else:
        flash("Your task is complete!", "success")


def convert_date_format(date):
    return datetime.strptime(
        datetime.strftime(date, "%Y-%m-%d, 00:00:00"), "%Y-%m-%d, %H:%M:%S"
    )


def string_to_datetime(date):
    return datetime.strptime(date, "%Y-%m-%d %H:%M:%S")


def datetime_to_string(date):
    return datetime.strftime(date, "%d-%m-%Y")


def date_for_despress_check(date_set):
    return datetime.strptime(str(date_set), "%Y-%m-%d")


def add_single_task(frequency, minutes, form, end, date, done=False):
    return Post(
        date=date,
        body=form.task.data,
        hour=form.start_time.data.hour,
        done=done,
        user_id=current_user.id,
        start_time=minutes,
        end_time=end,
        color=form.color.data,
        frequency=frequency,
    )


def calc_mins_height_and_end(form):
    minutes = (form.start_time.data.hour * 60) + form.start_time.data.minute
    height = ((form.end_time.data.hour * 60) + form.end_time.data.minute) - minutes
    end = (form.end_time.data.hour * 60) + form.end_time.data.minute
    return minutes, height, end


def commit_flush():
    db.session.commit()
    db.session.flush()
