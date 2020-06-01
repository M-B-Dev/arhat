from app.api import bp
from flask import jsonify, request, url_for, g, abort, current_app, render_template
from app.models import User, Post, Message
from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request
from datetime import datetime, timedelta
from app.email import send_email
import json

@bp.route('/tasks/<int:id>/<date>', methods=['GET'])
@token_auth.login_required
def tasks(id, date):
    user = User.query.get_or_404(id)
    data = User.to_collection_dict(user.get_daily_tasks(date), None, None, None)
    for task in data['items']:
        if task['to_date']:
            task['to_date'] = datetime.strftime(task['to_date'], "%d-%m-%Y")
    return jsonify(data)

@bp.route('/tasks/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_task(id):
    task = Post.query.get_or_404(id)
    user = User.query.get_or_404(task.user_id)
    data = request.get_json() or {}
    if check_start_and_end(data, task=task) is True:
        return bad_request('The start time must be earlier than the end time.')
    if data['to_date']:
        reformated_date = datetime.strptime(data['to_date'], "%d-%m-%Y")
        reformated_date = datetime.strftime(reformated_date, "%Y-%m-%d, 00:00:00")
        data['to_date'] = datetime.strptime(reformated_date, "%Y-%m-%d, %H:%M:%S")
    if data['single_event']:
        if task.exclude and task.exclude != id:
            data['frequency'] = 0
            task.from_dict(data)
        else:
            formated_date = datetime.strptime(data['page_date'], "%d-%m-%Y")
            formated_date = datetime.strftime(formated_date, "%Y-%m-%d, 00:00:00")
            formated_date = datetime.strptime(formated_date, "%Y-%m-%d, %H:%M:%S")
            new_task = Post(date=formated_date, user_id=task.user_id)
            new_task.from_dict(data)
            new_task.exclude = id
            task.exclude = task.id
            new_task.frequency = 0
            if task.date == new_task.date:
                task.done = True
            db.session.add(new_task)
    else:
        if task.exclude:
            parent_task = Post.query.get_or_404(task.exclude)
            if not parent_task.to_date:
                parent_task.frequency = data['frequency']
            tasks = [todo for todo in user.posts.all() if todo.exclude == task.exclude]
            for i, todo in enumerate(tasks):
                todo.body = data['body']
                todo.done = data['done']
                if data['done'] is True:
                    todo.frequency = 0
                elif data['frequency'] and int(data['frequency'])  == 0:
                    if i != len(tasks) - 1:
                        todo.done = True
                elif data['frequency'] and int(data['frequency']) > 0 and ((parent_task.date - todo.date).days % int(data['frequency']) != 0):
                    todo.done = True
                todo.color = data['color']
                todo.start_time = int(data['start_time'])
                todo.end_time = int(data['end_time'])
        else:
            if data['done'] is True:
                data['frequency'] = 0
            task.from_dict(data)
    db.session.commit()
    return jsonify(task.to_dict())

@bp.route('/tasks/<int:ident>/<date>', methods=['POST'])
def create_task(ident, date):
    frequency_days = 1
    data = request.get_json() or {}
    if check_start_and_end(data) is True:
        return bad_request('The start time must be earlier than the end time.')
    data['date'] = datetime.strptime(date, "%d-%m-%Y")
    data['user_id'] = int(ident)
    data['hour'] = 1    
    if data['frequency'] and data['frequency'] != 0:
        data['frequency'] = int(data['frequency'])
        inc = data['frequency']
    else:
        data['frequency'] = None
        inc = 1
    if 'done' in data and data['done'] is True:
        data['frequency'] = None
    if data['to_date'] and data['frequency']:
        reformated_date = datetime.strptime(data['to_date'], "%d-%m-%Y")
        reformated_date = datetime.strftime(reformated_date, "%Y-%m-%d, 00:00:00")
        data['to_date'] = datetime.strptime(reformated_date, "%Y-%m-%d, %H:%M:%S")
        frequency_days = (data['to_date'] - data['date']).days + 1
        data['frequency'] = None
    else:
        data['to_date'] = None
    for i in range(0, frequency_days, inc):
        data['date'] = data['date'] + timedelta(days=i)
        task = Post()
        task.from_dict(data)
        db.session.add(task)
        db.session.commit()
        db.session.flush()
        if i == 0:
            identifier = task.id
        if frequency_days > 1:
            task.exclude = identifier
            db.session.commit()
    user = User.query.get_or_404(ident)
    data = User.to_collection_dict(user.get_daily_tasks(date), None, None, None)
    return data

def check_start_and_end(data, task=None):
    if 'start_time' in data and 'end_time' in data and int(data['start_time']) > int(data['end_time']):
        return True
    elif 'start_time' in data and task and int(data['start_time']) > task.end_time:
        return True
    elif 'end_time' in data and task and int(data['end_time']) < task.start_time:
        return True
