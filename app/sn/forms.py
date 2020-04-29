from wtforms import(
    StringField, 
    SubmitField, 
    TextAreaField, 
    IntegerField
    )

from wtforms.validators import(
    DataRequired, 
    ValidationError, 
    Email, 
    Length, 
    NumberRange
    )

from flask_wtf.file import FileField, FileAllowed

from flask_login import current_user

from flask_wtf import FlaskForm

from app.models import User


class UpdateAccountForm(FlaskForm):
    """Allows a user to update their account info
    
    Threshold: depression percentage threshold. Any depression 
    percentage calculation that falls below this vale will 
    trigger contacts to be informed. 
    Days: The number of previous days that will be checked 
    for incomplete tasks.
    """

    username = StringField(
        'Username', 
        validators=[DataRequired()]
        )
    email = StringField(
        'Email', 
        validators=[DataRequired(), 
        Email()]
        )
    picture = FileField(
        'Update Profile Picture', 
        validators=[FileAllowed(['jpg', 'png', 'jpeg'])]
        )
    threshold = IntegerField(
        'Threshold', 
        validators=[DataRequired(), 
        NumberRange(min=0, max=100, message="Must be between 0 and 100")]
        )
    days = IntegerField(
        'Days', 
        validators=[DataRequired()]
        )
    submit = SubmitField(
        'Update'
        )


    def validate_username(self, username):
        """checks that the username is available"""
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Please use a different username.')


    def validate_email(self, email):
        """Check that the email has not been used before"""
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Please use a different email address.')


class MessageForm(FlaskForm):
    """Allows a user to input a message for another user."""
    message = TextAreaField(
        'Message', 
        validators=[DataRequired(), Length(min=0, max=140)]
        )
    submit = SubmitField(
        'Submit'
        )


class SearchForm(FlaskForm):
    """Allows a user ot search for other users."""

    search = StringField(
        'Search', 
        validators=[DataRequired(), Length(min=0, max=140)]
        )
    submit = SubmitField(
        'Submit'
        )