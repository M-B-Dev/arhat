from flask import current_app, render_template

from app.email import send_email


def send_password_reset_email(user):
    """

    Sends an email containing a link to reset the users password.
    user: should be the user object of the requester
    send-email: see app/email
    """
    
    token = user.get_reset_password_token()
    send_email(
        '[Template] Reset Your Password',
        sender=current_app.config['ADMINS'][0],
        recipients=[user.email],
        text_body=render_template(
            'email/reset_password.txt',
            user=user, 
            token=token
            ),
        html_body=render_template(
            'email/reset_password.html',
            user=user,
            token=token
            )
        )
