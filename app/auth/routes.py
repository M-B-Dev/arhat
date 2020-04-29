from flask_login import current_user, login_user, logout_user, login_required

from flask import render_template, flash, redirect, url_for, request

from werkzeug.urls import url_parse

from app.models import User

from app.auth import bp

from app import db

from app.auth.email import send_password_reset_email

from app.auth.forms import(
    ResetPasswordRequestForm, 
    LoginForm, 
    RegistrationForm, 
    ResetPasswordForm
    )


@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Logs a user in"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index', date_set="ph"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(f'Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.index', date_set='ph')
        return redirect(url_for('main.index', date_set='ph'))
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
@login_required
def logout():
    """Log user out"""
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """Allows a new user ot register"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash(
            f"""Congratulations {form.username.data}, 
            you are now a registered user!""", 
            'success'
            )
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', title='Register', form=form)

@bp.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    """requests a reset password token email"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit() \
            and User.query.filter_by(email=form.email.data).first():
        send_password_reset_email(
            User.query.filter_by(email=form.email.data).first()
            )
        flash(f'Check your email for the instructions to reset your password', 
            "warning"
            )
        return redirect(url_for('auth.login'))
    return render_template(
        'auth/reset_password_request.html',
        title='Reset Password', 
        form=form
        )

@bp.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """generates a reset password token"""
    if current_user.is_authenticated:
        return redirect(url_for('main.index', date_set="ph"))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('auth.login'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('auth.login'))
    return render_template('auth/.html', form=form)