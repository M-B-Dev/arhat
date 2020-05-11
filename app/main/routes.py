import json
from datetime import datetime

from flask import (
    Response,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from pywebpush import webpush

from app import db
from app.main import bp
from app.main.forms import DateForm, TaskForm
from app.models import Post, User


@bp.route("/", methods=["GET", "POST"])
def home():
    """This reroutes to index with the date_set argument."""
    return redirect(url_for("main.index", date_set="ph"))


@bp.route("/index/<date_set>", methods=["GET", "POST"])
@login_required
def index(date_set):
    """
    Render the index page.

    date_set: argument that is used to retreive tasks for
    a specific date or, if set to 'ph', will default to today's date.
    """
    date_form = DateForm()
    if date_form.validate_on_submit():
        return redirect(
            url_for(
                "main.index", 
                date_set=datetime_to_string(date_form.datepicker.data)
            )
        )
    form = TaskForm()
    date = set_date(date_set)
    today = False
    if convert_date_format(datetime.utcnow()) == date:
        today = True
    current_user.check_if_depression_sent(date)
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


@bp.route("/new_task/", methods=["GET", "POST"])
@login_required
def new_task():
    """Creates a new todo task."""
    new_task = Post()
    new_task.form = TaskForm()
    if not new_task.form.validate_on_submit():
        return redirect(url_for("main.index", date_set="ph"))
    else:
        new_task.calc_mins_height_and_end()
        if new_task.minutes > new_task.end:
            return redirect(url_for("main.index", date_set="ph"))
        new_task.set_frequency()
        if new_task.form.frequency.data and new_task.form.to_date.data:
            new_task.to_date = convert_date_format(new_task.form.to_date.data)
            new_task.date = new_task.string_to_datetime(new_task.form.date.data)
            if new_task.to_date > new_task.date:
                new_task.add_multiple_tasks()
                flash("Your tasks are now live!", "success")
            else:
                return redirect(url_for("main.index", date_set="ph"))
        elif not new_task.form.to_date.data:
            task_to_be_added = new_task.add_single_task(
                date=new_task.string_to_datetime(new_task.form.date.data),
                frequency=new_task.form.frequency.data,
            )
            db.session.add(task_to_be_added)
            new_task.commit_flush()
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
    """
    Edits a to-do task from modal input.

    Can be a single task or multiple, related tasks.
    """

    edit_task = Post()
    edit_task.form = TaskForm()
    edit_task.task_to_be_edited = current_user.posts.filter_by(
        id=int(edit_task.form.ident.data)
    ).first()
    if not edit_task.form.validate_on_submit():
        return redirect(url_for("main.index", date_set="ph"))
    else:
        edit_task.calc_mins_height_and_end()
        if edit_task.form.single_event.data is True:
            if (
                edit_task.task_to_be_edited.exclude
                and edit_task.task_to_be_edited.exclude
                != int(edit_task.form.ident.data)
            ):
                edit_task.edit_single_task()
            else:
                edit_task.edit_single_freq_task()
        else:
            if edit_task.task_to_be_edited.exclude:
                edit_task.edit_all_freq_parent_and_child_tasks()
            else:
                edit_task.edit_all_tasks()
        db.session.commit()
        return jsonify({"id": edit_task.form.ident.data})


@bp.route("/update_task/", methods=["GET", "POST"])
@login_required
def update_task():
    """Updates a to-do task from dragging or resizing."""
    if request.method == "POST":
        data = request.get_json()
        task = Post.query.filter_by(id=int(data["id"])).first()
        height = "".join([n for n in data["height"] if n.isnumeric()])
        top = "".join([n for n in data["top"] if n.isnumeric()])
        task.start_time = int(top)
        task.end_time = int(height) + int(top)
        db.session.commit()
    return jsonify({"task": task.body})


@bp.route("/check", methods=["GET", "POST"])
@login_required
def check():
    """
    Checks if any tasks are due.
    
    If tasks are due a notification is triggered.
    """

    if current_user.subscribed and str(request.args.get("id")).isnumeric():
        ident = int(request.args.get("id"))
        task = current_user.posts.filter_by(id=ident).first()
        webpush(
            subscription_info=json.loads(User.query.all()[0].subscription),
            data=f"You need to {task.body}",
            vapid_private_key=current_app.config["VAPID_PRIVATE_KEY"],
            vapid_claims=current_app.config["VAPID_CLAIMS"],
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


def set_date(date_set):
    """
    Sets date on rendering of index depending on value passed in on POST.
    
    ph: placeholder - will render today's date.
    """
    if date_set == "ph":
        return convert_date_format(datetime.utcnow())
    else:
        return datetime.strptime(date_set, "%d-%m-%Y")


def convert_date_format(date):
    """Converts a datetime object to the full date format as string."""
    return datetime.strptime(
        datetime.strftime(date, "%Y-%m-%d, 00:00:00"), "%Y-%m-%d, %H:%M:%S"
    )


def datetime_to_string(date):
    """Converts datetime to string, short version."""
    return datetime.strftime(date, "%d-%m-%Y")
