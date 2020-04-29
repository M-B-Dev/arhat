from wtforms import(
    StringField, 
    PasswordField, 
    BooleanField, 
    SubmitField, 
    )

from wtforms.validators import(
    DataRequired, 
    ValidationError, 
    Email, 
    EqualTo, 
    Length
    )

from flask_wtf import FlaskForm

from app.models import User


class LoginForm(FlaskForm):
    """Allows an existing user ot enter login info"""

    username = StringField(
        'Username', 
        validators=[DataRequired()]
        )
    password = PasswordField(
        'Password', 
        validators=[DataRequired()]
        )
    remember_me = BooleanField(
        'Remember Me'
        )
    submit = SubmitField(
        'Sign In'
        )

class RegistrationForm(FlaskForm):
    """Allows a new user to register"""

    username = StringField(
        'Username', 
        validators=[DataRequired(), 
        Length(min=2, max=20)]
        )
    email = StringField(
        'Email', 
        validators=[DataRequired(), Email()]
        )
    password = PasswordField(
        'Password', 
        validators=[DataRequired(), Length(min=9)]
        )
    password2 = PasswordField(
        'Repeat Password', 
        validators=[DataRequired(), EqualTo('password')]
        )
    submit = SubmitField(
        'Register'
        )

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class ResetPasswordRequestForm(FlaskForm):
    """Allows a user to request their password to be reset"""

    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')

class ResetPasswordForm(FlaskForm):
    """Allows a user to add details to enter a new password and reset it"""

    password = PasswordField(
        'Password', 
        validators=[DataRequired()]
        )
    password2 = PasswordField(
        'Repeat Password', 
        validators=[DataRequired(), EqualTo('password')]
        )
    submit = SubmitField(
        'Request Password Reset'
        )