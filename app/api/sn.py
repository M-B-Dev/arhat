from app.api import bp
from flask import jsonify, request, url_for, g, abort, current_app, render_template
from app.models import User, Post, Message
from app import db
from app.api.auth import token_auth
from app.api.errors import bad_request
from datetime import datetime, timedelta
from app.email import send_email
import json

@bp.route('/follow/<int:id>/<user_id>', methods=['POST'])
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

@bp.route('/unfollow/<int:id>/<user_id>', methods=['POST'])
@token_auth.login_required
def unfollow(id, user_id):
    user = User.query.filter_by(id=id).first_or_404()
    current_user = User.query.filter_by(id=user_id).first_or_404()
    current_user.unfollow(user)
    db.session.commit()
    return jsonify('success')

@bp.route('/messages/<msg_type>/<int:id>', methods=['GET'])
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

@bp.route('/send/<int:id>/<user_id>/<body>', methods=['POST'])
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