from threading import Thread

from flask_mail import Message

from flask import current_app

from app import mail


def send_async_email(app, msg):
    """Sends email outside of current_app context."""
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    """Sends threaded email."""
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(
        target=send_async_email, args=(current_app._get_current_object(), msg)
    ).start()
