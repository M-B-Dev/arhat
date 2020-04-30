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
    TaskForm, 
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
    date_form = DateForm()
    if date_form.validate_on_submit():
        return redirect(url_for(
            'main.index', 
            date_set=datetime.strftime(date_form.datepicker.data, '%d-%m-%Y')
            ))
    form = TaskForm()
    date_form = DateForm()
    date = set_date(date_set)
    today = False
    if datetime.strptime(
            datetime.strftime(datetime.utcnow(), "%Y-%m-%d, 00:00:00"), 
            "%Y-%m-%d, %H:%M:%S"
            ) == date:
        today = True
    check_depression_on_index(date)
    date_form.datepicker.data = date
    all_frequency_tasks = current_user.posts.filter(
        Post.frequency != None
        ).all()
    todos = current_user.posts.filter_by(date=date)
    exclusions = [todo.exclude for todo in todos if todo.exclude]
    frequency_tasks = [task for task in all_frequency_tasks \
        if task.frequency > 0 \
        and (date-task.date).days > 0 \
        and ((date-task.date).days % task.frequency) == 0 \
        and task.date < date \
        and task.id not in exclusions]
    tasks = {}
    task_hours = []
    for todo in todos:
        if todo.done == False:
            task_hours.append(todo.hour)
            tasks[todo.hour] = todo.body
    return render_template(
        "index.html", 
        frequency_tasks=frequency_tasks,
        today=today,
        todos=todos,
        date_set=date_set, 
        tasks=tasks, 
        task_hours=task_hours, 
        title='Home Page', 
        form=form, 
        user=current_user, 
        date_form=date_form
        )

@bp.route('/new_task/', methods=['GET', 'POST'])
@login_required
def new_task():
    """Creates a new todo task."""
    form = TaskForm()
    if form.validate_on_submit():
        minutes = (form.start_time.data.hour * 60) \
            + form.start_time.data.minute
        height = ((form.end_time.data.hour * 60) \
            + form.end_time.data.minute) - minutes
        if form.frequency.data == 0:
            frequency = None
        else:
            frequency = form.frequency.data
            if form.to_date.data:
                to_date = datetime.strptime(
                        datetime.strftime(form.to_date.data, 
                        "%Y-%m-%d, 00:00:00"), 
                        "%Y-%m-%d, %H:%M:%S"
                        )
                date = datetime.strptime(form.date.data, "%Y-%m-%d %H:%M:%S")
                if to_date > date:
                    for i in range((to_date-date).days, -1, -1):
                        task_to_be_added = Post(
                            date = date + timedelta(days=i),
                            body=form.task.data, 
                            hour= form.start_time.data.hour,
                            done=False,
                            user_id=current_user.id, 
                            start_time=(form.start_time.data.hour * 60) \
                                + form.start_time.data.minute,
                            end_time=(form.end_time.data.hour * 60) \
                                + form.end_time.data.minute,
                            color=form.color.data,
                            frequency=0
                            )
                        db.session.add(task_to_be_added)
                        db.session.commit()
                        db.session.flush()
                        if i == (to_date-date).days:
                            ident = task_to_be_added.id
                        task_to_be_added.exclude = ident
                        db.session.commit()
                else:
                    ident = 0
                flash('Your tasks are now live!', 'success')
                return jsonify({
                    'minutes' : minutes, 
                    'height' : height, 
                    'task' : form.task.data, 
                    'id' : ident, 
                    'color' : form.color.data, 
                    'frequency' : form.frequency.data
                    })
        task_to_be_added = Post(
                body=form.task.data, 
                hour= form.start_time.data.hour,
                done=False,
                date=datetime.strptime(form.date.data, "%Y-%m-%d %H:%M:%S"), 
                user_id=current_user.id, 
                start_time=(form.start_time.data.hour * 60) \
                    + form.start_time.data.minute,
                end_time=(form.end_time.data.hour * 60) \
                    + form.end_time.data.minute,
                color=form.color.data,
                frequency=frequency
                )
        db.session.add(task_to_be_added)
        db.session.commit()
        db.session.flush()
        ident = task_to_be_added.id
        flash('Your task is now live!', 'success')
    return jsonify({
        'minutes' : minutes, 
        'height' : height, 
        'task' : form.task.data, 
        'id' : ident, 
        'color' : form.color.data, 
        'frequency' : form.frequency.data
        })

@bp.route('/edit_task/', methods=['GET', 'POST'])
@login_required
def edit_task():
    form = TaskForm()
    if form.validate_on_submit():
        if form.single_event.data is True:
            task_to_be_edited = current_user.posts.filter_by(
                id=int(form.ident.data)
                ).first()
            if task_to_be_edited.exclude \
                    and task_to_be_edited.exclude != int(form.ident.data):
                minutes = (form.start_time.data.hour * 60) \
                    + form.start_time.data.minute
                height = ((form.end_time.data.hour * 60) \
                    + form.end_time.data.minute) - minutes
                task_to_be_edited = current_user.posts.filter_by(
                    id=int(form.ident.data)
                    ).first()
                task_to_be_edited.body = form.task.data
                task_to_be_edited.hour= form.start_time.data.hour
                task_to_be_edited.frequency = 0
                task_to_be_edited.done = form.done.data
                task_to_be_edited.color = form.color.data
                task_to_be_edited.user_id = current_user.id
                task_to_be_edited.start_time = (
                    form.start_time.data.hour * 60
                    ) + form.start_time.data.minute
                task_to_be_edited.end_time = (
                    form.end_time.data.hour * 60
                    ) + form.end_time.data.minute
                if task_to_be_edited.done is False:
                    flash('Your single task has been updated!', 'success')
                else:
                    flash('Your single task is complete!', 'success')
            else:
                task_to_be_added = Post(
                    body=form.task.data, 
                    hour= form.start_time.data.hour,
                    done=form.done.data,
                    date=datetime.strptime(
                        form.date.data, 
                        "%Y-%m-%d %H:%M:%S"
                        ), 
                    user_id=current_user.id, 
                    start_time=(form.start_time.data.hour * 60) \
                        + form.start_time.data.minute,
                    end_time=(form.end_time.data.hour * 60) \
                        + form.end_time.data.minute,
                    color=form.color.data,
                    frequency=0,
                    exclude=int(form.ident.data)
                    )
                task_to_be_edited.exclude = task_to_be_edited.id            
                if datetime.strptime(
                        form.date.data, "%Y-%m-%d %H:%M:%S"
                        ) == task_to_be_edited.date:
                    task_to_be_edited.done = True        
                db.session.add(task_to_be_added)
                if task_to_be_added.done is False:
                    flash('Your single task has been updated!', 'success')
                else:
                    flash('Your single task is complete!', 'success')
        else:
            task_to_be_edited = current_user.posts.filter_by(
                id=int(form.ident.data)
                ).first()
            minutes = (form.start_time.data.hour * 60) \
                + form.start_time.data.minute
            height = ((form.end_time.data.hour * 60) \
                + form.end_time.data.minute) - minutes
            if task_to_be_edited.exclude:
                parent_task = current_user.posts.filter_by(
                    id=task_to_be_edited.exclude
                    ).first()
                parent_task.frequency = form.frequency.data
                tasks = [task for task in current_user.posts.all() \
                    if task.exclude == task_to_be_edited.exclude]
                for task in tasks:
                    task.body = form.task.data
                    task.hour= form.start_time.data.hour
                    task.done = form.done.data
                    if form.done.data is True:
                        task.frequency = 0
                    elif ((parent_task.date-task.date).days \
                        % int(form.frequency.data)) != 0:
                        task.done = True
                    task.color = form.color.data
                    task.user_id = current_user.id
                    task.start_time = (form.start_time.data.hour * 60) \
                        + form.start_time.data.minute
                    task.end_time = (form.end_time.data.hour * 60) \
                        + form.end_time.data.minute
                flash('Your tasks have been updated!', 'success')
            else:
                task_to_be_edited.body = form.task.data
                task_to_be_edited.hour = form.start_time.data.hour
                task_to_be_edited.done = form.done.data
                task_to_be_edited.date = datetime.strptime(
                    form.date.data, "%Y-%m-%d %H:%M:%S"
                    )
                task_to_be_edited.user_id = current_user.id
                task_to_be_edited.start_time = (
                    form.start_time.data.hour * 60
                    ) + form.start_time.data.minute
                task_to_be_edited.end_time = (
                    form.end_time.data.hour * 60
                    ) + form.end_time.data.minute
                task_to_be_edited.color = form.color.data
                if task_to_be_edited.done == True:
                    task_to_be_edited.frequency = 0
                else:
                    task_to_be_edited.frequency = form.frequency.data
                if task_to_be_edited.done is False:
                    flash('Your task has been updated!', 'success')
                else:
                    flash('Your task is complete!', 'success')
        db.session.commit()
    return jsonify({'id' : form.ident.data})
    
@bp.route('/update_task/', methods=['GET', 'POST'])
@login_required
def update_task():
    if request.method == 'POST':
        data = request.get_json()
        task = Post.query.filter_by(id=int(data['id'])).first()
        height = ''.join([n for n in data['height'] if n.isnumeric()])
        top = ''.join([n for n in data['top'] if n.isnumeric()])
        task.start_time = int(top)
        task.end_time = int(height) + int(top)
        db.session.commit()
    return jsonify({'task' : task.body})

def add_sent_date(date):
    check_depression()
    current_user.sent_date = date
    db.session.commit()

def check_depression_on_index(date):
    today = datetime.strftime(datetime.utcnow().date(), "%Y-%m-%d %H:%M:%S")
    return add_sent_date(date)
    if current_user.sent_date:
        if str(current_user.sent_date) != today:
            add_sent_date(date)
    elif current_user.threshold and current_user.days:
        add_sent_date(today)

def set_date(date_set):
    if date_set == "ph":
        return datetime.strptime(
            datetime.strftime(datetime.utcnow(), "%Y-%m-%d, 00:00:00"), 
            "%Y-%m-%d, %H:%M:%S"
            )
    else:
        return datetime.strptime(date_set, "%d-%m-%Y")


@bp.route('/', methods=['GET', 'POST'])
def home():
    """This reroutes to index with the date_set argument."""
    return redirect(url_for('main.index', date_set='ph'))

def get_todays_tasks():
    return current_user.posts.filter_by(
        date=datetime.strptime(str(datetime.utcnow().date()), 
        "%Y-%m-%d")
        )

@bp.route('/check', methods=['GET', 'POST'])
@login_required
def check():
    """Checks if any tasks are due. 
    
    If tasks are due a notification is triggered. 
    """

    if current_user.subscribed and str(request.args.get('id')).isnumeric():
        ident = int(request.args.get('id'))
        task = current_user.posts.filter_by(id=ident).first()
        send_web_push(
            json.loads(User.query.all()[0].subscription), 
            f"You need to {task.body}"
            )
    else: 
        ident = False
    return jsonify({'id': ident})

@bp.route('/check_without_push', methods=['GET', 'POST'])
@login_required
def check_without_push():
    """This returns notifcation data of tasks due in JSON. 
    
    This differs from check_todo() in that no notifcation 
    is triggered. 
    """

    tasks = get_todays_tasks()
    for task in tasks:
        if task.hour == datetime.utcnow().hour and not task.done:
            return jsonify({
                'todo': task.body,
                'id': task.id
                })
    return jsonify({'todo': 'nothing'})

@bp.route('/complete', methods=['GET', 'POST'])
@login_required
def complete():
    """Clears completed tasks from the database and reloads index"""
    if request.args:
        if request.args.get("id").isnumeric():
            ident = int(request.args.get("id"))
            task = current_user.posts.filter_by(id=ident)
            task[0].done = True
            db.session.commit()
    return redirect(url_for('main.index', date_set="ph"))                        

def create_task(task, date_form):
    """Creates a task in the db"""
    task_to_be_added = Post(
                body=task.post.data, 
                hour=task.hour.data, 
                done=task.done.data,
                date=date_form.datepicker.data, 
                user_id=current_user.id
                )
    db.session.add(task_to_be_added)
    db.session.commit()
    flash('Your task is now live!', 'success')

def delete_or_update(user, date, Todo, form, date_form):
    """This deletes completed tasks or updates edited tasks."""
    todos = user.posts.filter_by(date=date)
    if Todo.done.data and todos.count() > 0:
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

def check_depression():
    """Checks if the percentage of complete tasks is lower than 
    the user set threshold. If lower then then messages and emails
    are sent to all users that the current user follows. 
    
    """
    all_frequency_tasks = current_user.posts.filter(
        Post.frequency != None
        ).all()
    outstanding_frequency_tasks = [
        task for task in all_frequency_tasks if task.done is False
        ]
    threshold = current_user.threshold
    date_set = datetime.utcnow().date()
    daily_percentage = 0
    number_of_days = current_user.days
    period_precentage = 0
    divide_days = 0
    for day in range(number_of_days):
        date_set = date_set - timedelta(days=1)
        daily_tasks = current_user.posts.filter_by(
            date=datetime.strptime(str(date_set), 
            "%Y-%m-%d")
            )
        done_tasks = 0
        freq_daily_tasks = 0
        freq_done_tasks = 0
        for freq_task in outstanding_frequency_tasks:
            if freq_task.frequency != 0 \
                and (datetime.strptime(
                    str(date_set
                    ), "%Y-%m-%d") - freq_task.date).days > 0 \
                and (datetime.strptime(
                    str(date_set), "%Y-%m-%d"
                    ) - freq_task.date).days % freq_task.frequency == 0:
                freq_daily_tasks += 1
                for tsk in daily_tasks:
                    if tsk.exclude == freq_task.id:
                        freq_daily_tasks -= 1    
        if daily_tasks.count() > 0:
            for task in daily_tasks:
                if task.done == True:
                    done_tasks += 1
            daily_percentage = (
                done_tasks/daily_tasks.count()+freq_daily_tasks
                )*100
            divide_days += 1
            period_precentage += daily_percentage
        elif freq_daily_tasks > 0:
            divide_days += 1
    if divide_days > 0:        
        period_precentage /= divide_days
    else:
        period_precentage = 100
    if period_precentage < threshold:
        for followed in current_user.followed.all():
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
    if not current_user.subscribed:
        current_user.subscribed = True
    else:
        current_user.subscribed = False
    db.session.commit()
    return redirect(url_for('sn.edit_profile'))