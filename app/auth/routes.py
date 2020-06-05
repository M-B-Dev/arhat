from flask import flash, redirect, render_template, request, url_for, current_app
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse

from app import db
from app.auth import bp
from app.auth.email import send_password_reset_email
from app.auth.forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordForm,
    ResetPasswordRequestForm,
)
from app.models import User

import json
from oauthlib.oauth2 import WebApplicationClient
import requests


@bp.route("/login_page", methods=["GET", "POST"])
def login_page():
    """Logs a user in"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index", date_set="ph"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash(f"Invalid username or password", "danger")
            return redirect(url_for("auth.login_page"))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("main.index", date_set="ph")
        return redirect(url_for("main.index", date_set="ph"))
    return render_template("auth/login.html", title="Sign In", form=form)


@bp.route("/logout")
@login_required
def logout():
    """Log user out"""
    logout_user()
    return redirect(url_for("auth.login_page"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    """Allows a new user ot register"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
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
            "success",
        )
        return redirect(url_for("main.index", date_set="ph"))
    return render_template("auth/register.html", title="Register", form=form)


@bp.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    """requests a reset password token email"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    form = ResetPasswordRequestForm()
    if (
        form.validate_on_submit()
        and User.query.filter_by(email=form.email.data).first()
    ):
        send_password_reset_email(User.query.filter_by(email=form.email.data).first())
        flash(
            f"Check your email for the instructions to reset your password", "warning"
        )
        return redirect(url_for("auth.login_page"))
    return render_template(
        "auth/reset_password_request.html", title="Reset Password", form=form
    )


@bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """generates a reset password token"""
    if current_user.is_authenticated:
        return redirect(url_for("main.index", date_set="ph"))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("auth.login_page"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash("Your password has been reset.")
        return redirect(url_for("auth.login_page"))
    return render_template("auth/.html", form=form)


def get_google_provider_cfg():
    """obtains google config data"""
    return requests.get(
        "https://accounts.google.com/.well-known/openid-configuration"
        ).json()


@bp.route('/login')
def login():
    """This initiates the google log in process."""
    url = request.base_url
    if url[4] != "s":
        url = "https" + url[4:]
    client = WebApplicationClient(current_app.config['GOOGLE_CLIENT_ID'])
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg[
        "authorization_endpoint"
        ]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=url + "/callback",
        scope=["openid", "email", "profile"],
        prompt='consent'
    )
    return redirect(request_uri)


@bp.route("/login/callback")
def callback():
    """
    
    This deals with the Google API token for user 
    authentification.
    """
    
    client = WebApplicationClient(
        current_app.config['GOOGLE_CLIENT_ID']
        )
    code = request.args.get("code")
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]
    if request.url[4] == 's':
        url = "https" + request.url[5:]
    else:
        url = "https" + request.url[4:]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=url,
        redirect_url=request.base_url,
        code=code
        )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(
            current_app.config['GOOGLE_CLIENT_ID'], 
            current_app.config['GOOGLE_CLIENT_SECRET']
            ),
        )
    client.parse_request_body_response(
        json.dumps(token_response.json())
        )
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(
        uri, 
        headers=headers, 
        data=body
        )
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["given_name"]
        if User.query.filter_by(email=users_email).first():
            user = User.query.filter_by(email=users_email).first()
            if user is None or not user.check_password(unique_id):
                return redirect(url_for('auth.login_page'))
            login_user(user, remember=False)
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('main.index', date_set="ph")
            return redirect(next_page)
        else:
            user = User(username=users_name, email=users_email)
            user.set_password(unique_id)
            db.session.add(user)
            db.session.commit()
    else:
        return "User email not available or not verified by Google.", 400
    return redirect(url_for("main.index", date_set="ph"))
