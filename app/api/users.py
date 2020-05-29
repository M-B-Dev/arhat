from app.api import bp
from flask import jsonify, request, url_for, g, abort, current_app, render_template
from app.models import User, Post, Message
from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request
from datetime import datetime
from app.email import send_email
import json

@bp.route('/users/<id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    if str(id)[0].isnumeric() is True:
        return jsonify(User.query.get_or_404(int(id)).to_dict())
    else:
        ids = id[1:]
        id_list = ids.split('A')
        id_list = list(dict.fromkeys(id_list))
        ids = [User.query.get_or_404(int(ident)).to_dict() for ident in id_list]
        return jsonify(ids)
            

@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)

@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
                                   'api.get_followers', id=id)
    return jsonify(data)

@bp.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
                                   'api.get_followed', id=id)
    return jsonify(data)

@bp.route('/users/<int:id>/penders', methods=['GET'])
@token_auth.login_required
def get_penders(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 100)
    data = User.to_collection_dict(user.pended, page, per_page,
                                   'api.get_penders', id=id)
    return jsonify(data)


@bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json() or {}
    if 'username' not in data or 'email' not in data or 'password' not in data:
        return bad_request('must include username, email and password fields')
    if User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user = User()
    user.from_dict(data, new_user=True)
    db.session.add(user)
    db.session.commit()
    response = jsonify(user.to_dict())
    response.status_code = 201
    response.headers['Location'] = url_for('api.get_user', id=user.id)
    return response

@bp.route('/users/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_user(id):
    user = User.query.get_or_404(id)
    data = request.get_json() or {}
    if 'username' in data and data['username'] != user.username and \
            User.query.filter_by(username=data['username']).first():
        return bad_request('please use a different username')
    if 'email' in data and data['email'] != user.email and \
            User.query.filter_by(email=data['email']).first():
        return bad_request('please use a different email address')
    user.from_dict(data, new_user=False)
    db.session.commit()
    return jsonify(user.to_dict())

@bp.route('/users/tasks/<int:id>/<date>', methods=['GET'])
@token_auth.login_required
def tasks(id, date):
    user = User.query.get_or_404(id)
    data = User.to_collection_dict(user.get_daily_tasks(date), None, None, None)
    return jsonify(data)

@bp.route('/users/tasks/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_task(id):
    task = Post.query.get_or_404(id)
    data = request.get_json() or {}
    if check_start_and_end(data, task=task) is True:
        return bad_request('The start time must be earlier than the end time.')
    task.from_dict(data)
    db.session.commit()
    return jsonify(task.to_dict())

@bp.route('/users/tasks/<int:ident>/<date>', methods=['POST'])
def create_task(ident, date):
    data = request.get_json() or {}
    if check_start_and_end(data) is True:
        return bad_request('The start time must be earlier than the end time.')
    task = Post()
    if 'start_time' in data and 'end_time' in data:
        data['date'] = date
        data['user_id'] = ident
        task.from_dict(data)
    else:
        return bad_request('You must include a start and an end time.')
    db.session.add(task)
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

@bp.route('/users/follow/<int:id>/<user_id>', methods=['POST'])
@token_auth.login_required
def follow_request(id, user_id):
    user = User.query.filter_by(id=id).first_or_404()
    current_user = User.query.filter_by(id=user_id).first_or_404()
    if user is None or current_user.is_following(user) or current_user.is_pending(user):
        return jsonify('failure')
    current_user.pend(user)
    token = user.get_follow_request_token()
    send_email(
        "[Arhat] Connection Request",
        sender=current_app.config["ADMINS"][0],
        recipients=[user.email],
        text_body=render_template(
            "email/follow_request.txt",
            user=user,
            follow_requester=current_user,
            token=token,
        ),
        html_body=render_template(
            "email/follow_request.html",
            user=user,
            follow_requester=current_user,
            token=token,
        ),
    )
    msg = Message(
        author=current_user,
        recipient=user,
        body="Check your email, I have sent you a connection request",
    )
    db.session.add(msg)
    db.session.commit()
    return jsonify('success')

@bp.route('/users/unfollow/<int:id>/<user_id>', methods=['POST'])
@token_auth.login_required
def unfollow(id, user_id):
    user = User.query.filter_by(id=id).first_or_404()
    current_user = User.query.filter_by(id=user_id).first_or_404()
    current_user.unfollow(user)
    db.session.commit()
    return jsonify('success')

@bp.route('/users/messages/<msg_type>/<int:id>', methods=['GET'])
@token_auth.login_required
def get_messages(id, msg_type):
    user = User.query.filter_by(id=id).first_or_404()
    if not user:
        return jsonify('failure')
    user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    if msg_type == "received":
        messages = user.messages_received.order_by(Message.timestamp.desc())
    if msg_type == "sent":
        messages = user.messages_sent.order_by(Message.timestamp.desc())
    data = User.to_collection_dict(messages, None, None, None)
    return jsonify(data)

@bp.route('/users/send/<int:id>/<user_id>/<body>', methods=['POST'])
@token_auth.login_required
def send_message(id, user_id, body):
    """Sends a private message to another user."""
    user = User.query.filter_by(id=int(id)).first_or_404()
    current_user = User.query.filter_by(id=int(user_id)).first_or_404()
    if not user or not current_user:
        return jsonify('failure')
    msg = Message(author=current_user, recipient=user, body=body)
    db.session.add(msg)
    db.session.commit()
    return jsonify('success')