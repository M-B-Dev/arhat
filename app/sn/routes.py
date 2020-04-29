from datetime import datetime

from PIL import Image

import secrets

import os

from flask import(
    render_template, 
    flash, 
    redirect, 
    url_for, 
    request, 
    current_app, 
    jsonify,  
    session
    )

from flask_login import current_user, login_required

from app.models import User, Message

from app.sn import bp

from app.email import send_email

from app.sn.forms import(
    UpdateAccountForm, 
    MessageForm, 
    SearchForm
    )

from app import db


def save_picture(form_picture):
    """This reformats an image into manageable a size and with dimensions.
    
    Also, this will delete any previous profile image from the db.
    """
    if current_user.image_file and current_user.image_file != 'default.jpg':
        os.remove(
            current_app.root_path \
            + '//static/profile_pics//' \
            + current_user.image_file
            )
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(
        current_app.root_path, 
        'static/profile_pics', 
        picture_fn
        )
    output_size = (250, 250)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """Renders the edit profile page."""
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.threshold = form.threshold.data
        current_user.days = form.days.data
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash(f'Your account has been updated', 'success')
        return redirect(url_for('sn.edit_profile'))
    elif request.method =="GET":
        if current_user.days:
            form.days.data = current_user.days
        if current_user.threshold:
            form.threshold.data = current_user.threshold
        form.username.data = current_user.username
        form.email.data = current_user.email
    if current_user.image_file:
        image_file = url_for(
            'static', 
            filename='profile_pics/' + current_user.image_file
            )
    else:
        image_file = url_for('static', filename='profile_pics/default.jpg')
    return render_template(
        'sn/edit_profile.html', 
        title='Edit Profile', 
        image_file=image_file, 
        form=form
        )

@bp.route('/contacts', methods=['GET', 'POST'])
@login_required
def contacts():
    """This renders a paginated page, with all users in the db."""
    user = User.query.filter_by(username=current_user.username).first_or_404()
    form = SearchForm()
    page = request.args.get('page', 1, type=int)
    if form.validate_on_submit():
        people_id = User.query.filter(
            User.id != current_user.id
            ).filter(
                User.username.like('%' + form.search.data + '%')
                )
        people_email = User.query.filter(
            User.id != current_user.id).filter(
                User.email.like('%' + form.search.data + '%')
                )
        people = [person_id for person_id in people_id]
        [people.append(person_email) for person_email in people_email]
        people = list(dict.fromkeys(people))
        return render_template(
            'sn/contacts.html', 
            user=user, 
            people=people, 
            form=form
            )
    else:
        people = User.query.filter(
            User.id != current_user.id
            ).order_by(
                User.username
                )
    people = people.paginate(
        page, 
        current_app.config['POSTS_PER_PAGE'], 
        False
        )
    next_url = url_for('sn.contacts', page=people.next_num) \
        if people.has_next else None
    prev_url = url_for('sn.contacts', page=people.prev_num) \
        if people.has_prev else None
    return render_template(
        'sn/contacts.html', 
        user=user, 
        people=people.items, 
        form=form, 
        next_url=next_url, 
        prev_url=prev_url
        )

@bp.route('/following', methods=['GET', 'POST'])
@login_required
def following():
    """renders a page of users who the current.user is following."""
    user = User.query.filter_by(username=current_user.username).first_or_404()
    people = current_user.followed.all()
    return render_template('sn/following.html', user=user, people=people)

@bp.route('/followers', methods=['GET', 'POST'])
@login_required
def followers():
    """renders a page of users who follow the current.user."""
    user = User.query.filter_by(username=current_user.username).first_or_404()
    people = current_user.followers.all()
    return render_template('sn/followers.html', user=user, people=people)

@bp.route('/follow_request/<username>', methods=['GET', 'POST'])
@login_required
def follow_request(username):
    """Sends a token to the user which the current user has requested to follow. 
    
    Emails the token and messgaes the user.
    """

    user = User.query.filter_by(username=username).first_or_404()
    if user is None:
        flash('User {} not found.'.format(username))
        return redirect(url_for(
            'sn.contacts', 
            username=current_user.username
            ))
    if user == current_user:
        flash(f'You cannot follow yourself!', 'warning')
        return redirect(url_for(
            'sn.contacts', 
            username=current_user.username
            ))
    current_user.pend(user)
    flash(f'your follow request for {username} has been sent!', 'warning')
    token = user.get_follow_request_token()
    send_email('[Template] Connection Request',
               sender=current_app.config['ADMINS'][0],
               recipients=[user.email],
               text_body=render_template(
                   'email/follow_request.txt',
                    user=user, 
                    follow_requester=current_user, 
                    token=token
                    ),
               html_body=render_template(
                   'email/follow_request.html',
                    user=user, 
                    follow_requester=current_user, 
                    token=token
                    )
                )
    msg = Message(
        author=current_user, 
        recipient=user,
        body="Check your email, I have sent you a connection request"
        )
    db.session.add(msg)
    db.session.commit()
    
    return redirect(url_for('sn.contacts', username=current_user.username))

@bp.route(
    '/follow/<username>/<follow_requester>/<token>', methods=['GET', 'POST']
    )
def follow(username, follow_requester, token):
    """Receives the token from the user and sets up relationship"""
    user = User.query.filter_by(username=username).first()
    follow_user = User.query.filter_by(username=follow_requester).first()
    verified = User.verify_follow_request_token(token)
    if not verified:
        flash(f'Token not valid.', 'danger')
        return render_template('sn/follow.html', title='Follow')
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return render_template('sn/follow.html', title='Follow')
    if user == follow_requester:
        flash(f'You cannot follow yourself!', 'danger')
        return render_template('sn/follow.html', title='Follow')
    if follow_user.is_following(user):
        flash(f'You are already following this person!', 'warning')
        return render_template('sn/follow.html', title='Follow')
    follow_user.follow(user)
    follow_user.unpend(user)
    db.session.commit()
    flash(f'You are following {follow_requester}!', 'success')
    return render_template('sn/follow.html', title='Follow')

@bp.route('/unfollow/<username>')
@login_required
def unfollow(username):
    """Allows the curret user to unfollow a user"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'User {username} not found.', 'danger')
        return redirect(url_for('sn.contacts'))
    if user == current_user:
        flash(f'You cannot unfollow yourself!', 'danger')
        return redirect(url_for('sn.contacts', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are not following {username}.', 'danger')
    return redirect(url_for('sn.contacts', username=username))

@bp.route('/send_message/<recipient>', methods=['GET', 'POST'])
@login_required
def send_message(recipient):
    """Sends a private message to another user."""
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(
            author=current_user, 
            recipient=user,
            body=form.message.data
            )
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent.', 'success')
        return redirect(url_for('sn.sent_messages'))
    return render_template(
        'sn/send_message.html', 
        title='Send Message',
        form=form, 
        recipient=recipient
        )

@bp.route('/reply/<recipient>/<ident>', methods=['GET', 'POST'])
@login_required
def reply(recipient, ident):
    """Allows a user to reply to a specific message."""
    user = User.query.filter_by(username=recipient).first_or_404()
    form = MessageForm()
    message = Message.query.filter_by(id=ident).first_or_404()
    time = message.timestamp.strftime('%d/%m/%Y %H:%M:%S')
    form.message.data = f"Quote: {message.body}, sent on {time}"
    if form.validate_on_submit():
        msg = Message(author=current_user, recipient=user,
                      body=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent.', 'success')
        return redirect(url_for('sn.sent_messages'))
    return render_template('sn/reply.html', title='Send Message',
                           form=form, recipient=recipient)

@bp.route('/messages')
@login_required
def messages():
    """Renders a page of private receievd messages."""
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    messages = current_user.messages_received.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('sn.messages', page=messages.next_num) \
        if messages.has_next else None
    prev_url = url_for('sn.messages', page=messages.prev_num) \
        if messages.has_prev else None
    return render_template(
        'sn/messages.html', 
        messages=messages.items, 
        next_url=next_url, 
        prev_url=prev_url, 
        )

@bp.route('/sent_messages')
@login_required
def sent_messages():
    """Renders a page of paginated messages sent by the current user."""
    current_user.last_message_read_time = datetime.utcnow()
    db.session.commit()
    page = request.args.get('page', 1, type=int)
    sent_messages = current_user.messages_sent.order_by(
        Message.timestamp.desc()).paginate(
            page, current_app.config['POSTS_PER_PAGE'], False)
    sent_next_url = url_for(
        'sn.sent_messages', 
        page=sent_messages.next_num) \
        if sent_messages.has_next else None
    sent_prev_url = url_for(
        'sn.sent_messages', 
        page=sent_messages.prev_num) \
        if sent_messages.has_prev else None
    return render_template(
        'sn/sent_messages.html', 
        sent_messages=sent_messages.items,
        sent_next_url=sent_next_url, 
        sent_prev_url=sent_prev_url
        )