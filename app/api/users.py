from app.api import bp
from flask import jsonify, request, url_for, g, abort
from app.models import User, Post
from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request

@bp.route('/users/<int:id>', methods=['GET'])
@token_auth.login_required
def get_user(id):
    return jsonify(User.query.get_or_404(id).to_dict())

@bp.route('/users', methods=['GET'])
@token_auth.login_required
def get_users():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(User.query, page, per_page, 'api.get_users')
    return jsonify(data)

@bp.route('/users/<int:id>/followers', methods=['GET'])
@token_auth.login_required
def get_followers(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followers, page, per_page,
                                   'api.get_followers', id=id)
    return jsonify(data)

@bp.route('/users/<int:id>/followed', methods=['GET'])
@token_auth.login_required
def get_followed(id):
    user = User.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = User.to_collection_dict(user.followed, page, per_page,
                                   'api.get_followed', id=id)
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
    response = jsonify(task.to_dict())
    response.status_code = 201
    return response

def check_start_and_end(data, task=None):
    if 'start_time' in data and 'end_time' in data and int(data['start_time']) > int(data['end_time']):
        return True
    elif 'start_time' in data and task and int(data['start_time']) > task.end_time:
        return True
    elif 'end_time' in data and task and int(data['end_time']) < task.start_time:
        return True