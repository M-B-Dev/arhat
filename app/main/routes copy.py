from datetime import datetime, date, timedelta

import json

from flask import(
    render_template, 
    flash, 
    redirect, 
    url_for, 
    request, 
    current_app, 
    jsonify, 
    Response, 
    session
    )

from flask_login import current_user, login_required

from pywebpush import webpush

from app.models import User, Post, Message

from app.main import bp

from app.email import send_email

from app.main.forms import(
    PostForm, 
    DateForm
    )

from app import db


@bp.route('/index/<date_set>', methods=['GET', 'POST'])
@login_required
def index(date_set):
    """Render the index page.

    date_set: argument that is used to retreive tasks for 
    a specific date or, if set to 'ph', will default to today's date.

    """
    if not current_user.username:
        return redirect(url_for('login'))

    hours = [
            {"hr": 1},{"hr": 2},{"hr": 3},{"hr": 4},
            {"hr": 5},{"hr": 6},{"hr": 7},{"hr": 8},
            {"hr": 9},{"hr": 10},{"hr": 11},{"hr": 12},
            {"hr": 13},{"hr": 14},{"hr": 15},{"hr": 16},
            {"hr": 17},{"hr": 18},{"hr": 19},{"hr": 20},
            {"hr": 21},{"hr": 22},{"hr": 23},{"hr": 0}
            ]

    form = PostForm(Todos=hours)
    user = current_user()
    date_form = DateForm()
    if date_form.validate_on_submit():
        return redirect(url_for('main.index', date_set=date_form.date.data))
    if date_set == "ph":
        date_set = datetime.utcnow().date()
        date = datetime.strptime(
            datetime.strftime(date_set, "%Y-%m-%d, %H:%M:%S"), 
            "%Y-%m-%d, %H:%M:%S"
            )
    else:
        date = datetime.strptime(date_set, "%Y-%m-%d")
    today = datetime.utcnow().date()
    today = datetime.strptime(
        datetime.strftime(today, "%Y-%m-%d, %H:%M:%S"), 
        "%Y-%m-%d, %H:%M:%S"
        )
    if current_user.sent_date:
        if str(current_user.sent_date) != str(today):
            check_depression()
            current_user.sent_date = date
            db.session.commit()
    else:
        check_depression()
        current_user.sent_date = today
        db.session.commit()
    date_form.date.data = date
    todos = user.posts.filter_by(date=date)
    tasks = {}
    task_hours = []
    for todo in todos:
        if todo.done == False:
            task_hours.append(todo.hour)
            tasks[todo.hour] = todo.body
    if form.validate_on_submit():
        for Todo in form.Todos:
            delete_or_update(user, date, Todo, form, date_form)
        return redirect(url_for('main.index', date_set=date_set))
    return render_template(
        "index.html", 
        date_set=date_set, 
        tasks=tasks, 
        task_hours=task_hours, 
        title='Home Page', 
        form=form, 
        user=current_user, 
        date_form=date_form
        )

@bp.route('/', methods=['GET', 'POST'])
def home():
    """This reroutes to index with the date_set argument."""
    return redirect(url_for('main.index', date_set='ph'))

@bp.route('/check', methods=['GET', 'POST'])
@login_required
def check_todos():
    """Checks if any tasks are due. 
    
    If tasks are due a notification is triggered. 
    """

    if current_user.is_authenticated:
        user = User.query.filter_by(
            username=current_user.username
            ).first_or_404()
        date_set = datetime.utcnow().date()
        date = datetime.strptime(
            datetime.strftime(date_set, "%Y-%m-%d, %H:%M:%S"), 
            "%Y-%m-%d, %H:%M:%S"
            )
        todos = user.posts.filter_by(date=date)
        for todo in todos:
            if str(todo.hour) == str(datetime.utcnow().hour+1) \
                    and todo.done == False:
                if current_user.subscribed == True:
                    send_web_push(
                        json.loads(User.query.all()[0].subscription), 
                        f"You need to {todo.body}"
                        )
                return jsonify({
                    'todo': todo.body,
                    'id': todo.id
                    })
    return jsonify({'todo': 'nothing'})

@bp.route('/check2', methods=['GET', 'POST'])
def check_todos2():
    """This returns notifcation data of tasks due in JSON. 
    
    This differs from check_todo() in that no notifcation 
    is triggered. 
    """

    if current_user.is_authenticated:
        user = User.query.filter_by(
            username=current_user.username
            ).first_or_404()
        date_set = datetime.utcnow().date()
        date = datetime.strptime(
            datetime.strftime(date_set, "%Y-%m-%d, %H:%M:%S"), 
            "%Y-%m-%d, %H:%M:%S"
            )
        todos = user.posts.filter_by(date=date)
        for todo in todos:
            if str(todo.hour) == str(datetime.utcnow().hour+1) \
                    and todo.done == False:
                return jsonify({
                    'todo': todo.body,
                    'id': todo.id
                    })
    return jsonify({'todo': 'nothing'})

@bp.route('/complete', methods=['GET', 'POST'])
def todo_complete():
    """Clears completed tasks from the database and reloads index"""
    if request.args and current_user.is_authenticated:
        if request.args.get("id").isnumeric() is False:
            return redirect(url_for('main.index', date_set="ph"))
        ident = int(request.args.get("id"))
        user = User.query.filter_by(
            username=current_user.username
            ).first_or_404()
        todo = user.posts.filter_by(id=ident)
        todo[0].done = True
        db.session.commit()
    return redirect(url_for('main.index', date_set="ph"))                        

def create_task(Todo, date_form):
    """Creates a task in the db"""
    task = Post(
                body=Todo.post.data, 
                hour=Todo.hour.data, 
                done=Todo.done.data,
                date=date_form.date.data, 
                user_id=current_user.id
                )
    db.session.add(task)
    db.session.commit()
    flash('Your task is now live!', 'success')

def delete_or_update(user, date, Todo, form, date_form):
    """This deletes completed tasks or updates edited tasks."""
    todos = user.posts.filter_by(date=date)
    if Todo.done.data == True:
        if todos.count() > 0:
            for post in todos:
                if post.hour == Todo.hour.data:
                    post.done = True
                    db.session.commit()                        
                    flash('You have completed this task', 'success')
    elif Todo.validate_on_submit() and len(Todo.post.data) > 0:
        for post in todos:
            if post.hour == Todo.hour.data:
                post.body = Todo.post.data
                post.done = False
                db.session.commit()
                return
        if todos.count() < 1:
            create_task(Todo, date_form)
            return
        else:
            create_task(Todo, date_form)
            return

@bp.route('/check_depression')
def check_depression():
    """Checks if the percentage of complete tasks is lower than 
    the user set threshold. If lower then then messages and emails
    are sent to all users that the current user follows. 
    
    """

    if current_user.is_authenticated:
        user = User.query.filter_by(
            username=current_user.username
            ).first_or_404()
        if current_user.threshold:
            threshold = current_user.threshold
        else:
            threshold = 0
        date_set = datetime.utcnow().date()
        daily_percentage = 0
        if current_user.days:
            number_of_days = current_user.days
        else:
            number_of_days = 7
        period_precentage = 0
        divide_days = 0
        for day in range(number_of_days):
            date_set = date_set - timedelta(days=1)
            try:
                date = datetime.strptime(
                    datetime.strftime(date_set, "%Y-%m-%d, %H:%M:%S"), 
                    "%Y-%m-%d, %H:%M:%S"
                    )
            except:
                date = datetime.strptime(date_set, "%Y-%m-%d")
            daily_tasks = user.posts.filter_by(date=date)
            done_tasks = 0
            if daily_tasks.count() > 0:
                for task in daily_tasks:
                    if task.done == True:
                        done_tasks += 1
                daily_percentage = (done_tasks/daily_tasks.count())*100
                divide_days += 1
                period_precentage += daily_percentage
        if divide_days > 0:        
            period_precentage /= divide_days
        else:
            period_precentage = 100
        if period_precentage < threshold:
            for followed in user.followed.all():
                send_email(
                    "Urgent", 
                    current_app.config['ADMINS'][0], 
                    [followed.email], 
                    f"please contact {current_user.username}", 
                    html_body=None
                    )
                msg = Message(
                    author=current_user, 
                    recipient=followed,
                    body=f"please contact {current_user.username}"
                    )
                db.session.add(msg)
                db.session.commit()
    return redirect(url_for('main.index', date_set="ph"))

@bp.route('/subscribe/', methods=['GET', 'POST'])
def subscribe():
    """Gets and stores a user notification subscription in the db."""
    subscription = request.json.get('sub_token')
    User.query.all()[0].subscription = json.dumps(subscription)
    db.session.commit()
    return redirect(url_for('sn.edit_profile'))

@bp.route("/subscription/", methods=["GET", "POST"])
def subscription():
    """POST creates a subscription.

    GET returns vapid public key which clients uses 
    to send around push notification.
    """

    if request.method == "GET":
        return Response(
            response=json.dumps(
                {"public_key": current_app.config['VAPID_PUBLIC_KEY']}
                ),
            headers={"Access-Control-Allow-Origin": "*"}, 
            content_type="application/json"
            )
    subscription_token = request.get_json("subscription_token")
    return Response(status=201, mimetype="application/json")

def send_web_push(subscription_information, message_body):
    """Triggers notifications by initializing JS Service Worker"""
    return webpush(
        subscription_info=subscription_information,
        data=message_body,
        vapid_private_key=current_app.config['VAPID_PRIVATE_KEY'],
        vapid_claims=current_app.config['VAPID_CLAIMS']
    )

@bp.route('/unsubscribe', methods=['GET', 'POST'])
def unsubscribe():
    """turns off user notifications."""
    current_user.subscribed = False
    current_user.subscription = None
    db.session.commit()
    return redirect(url_for('main.index', date_set="ph"))

@bp.route('/sub', methods=['GET', 'POST'])
def flask_subscribe():
    """Sets user notifications to off in the database."""
    if current_user.subscribed == False:
        current_user.subscribed = True
    else:
        current_user.subscribed = False
    db.session.commit()
    return redirect(url_for('sn.edit_profile'))