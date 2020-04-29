from wtforms import(
    FormField, 
    FieldList, 
    StringField, 
    BooleanField, 
    SubmitField, 
    IntegerField,
    DateField
    )

from wtforms.fields.html5 import TimeField

from wtforms.validators import DataRequired, Optional

from flask_wtf import FlaskForm


class TaskForm(FlaskForm):
    """Allows for multiple PostEntryForms to be generated through iteration.
    
    Todos: post, done an hour fields from PostEntryForm.
    """

    task = StringField('Describe your task', validators=[DataRequired()])
    done = BooleanField('Done')    
    start_time = TimeField('Start time', validators=[DataRequired()])
    end_time = TimeField('End time', validators=[DataRequired()])
    date = StringField()
    to_date = DateField('Repeat until', validators=[Optional()], format="%d-%m-%Y")
    color = StringField('Choose color')
    frequency = IntegerField('Enter how often you want this task ot repeat in days', validators=[Optional()])
    single_event = BooleanField('Just this event?')
    ident = IntegerField('id', validators=[Optional()])
    submit = SubmitField('Submit')


class DateForm(FlaskForm):
    """Allows a user to change the date of the visible to do list"""
    datepicker = DateField(validators=[DataRequired()], format="%d-%m-%Y")
    submit = SubmitField('Change Date')

