from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField, TextAreaField, SelectMultipleField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, URL

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')
    
    def __init__(self, *args, **kwargs):
        super(LoginForm, self).__init__(*args, **kwargs)
        # Ensure CSRF protection is properly setup

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=64)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    role_id = SelectField('Role', coerce=int, validators=[DataRequired()])
    locations = SelectMultipleField('Accessible Locations', coerce=int)
    is_active = BooleanField('Active')
    submit = SubmitField('Save')

class LocationForm(FlaskForm):
    name = StringField('Location Name', validators=[DataRequired(), Length(max=100)])
    address = StringField('Address', validators=[Length(max=255)])
    city = StringField('City', validators=[Length(max=100)])
    state = StringField('State/Province', validators=[Length(max=100)])
    country = StringField('Country', validators=[Length(max=100)])
    zipcode = StringField('ZIP/Postal Code', validators=[Length(max=20)])
    submit = SubmitField('Save')

class CameraForm(FlaskForm):
    name = StringField('Camera Name', validators=[DataRequired(), Length(max=100)])
    rtsp_url = StringField('RTSP URL', validators=[DataRequired(), URL()])
    shinobi_id = StringField('Shinobi ID', validators=[Length(max=100)])
    shinobi_api_key = StringField('Shinobi API Key', validators=[Length(max=100)])
    shinobi_group_key = StringField('Shinobi Group Key', validators=[Length(max=100)])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    is_ptz = BooleanField('PTZ Camera')
    submit = SubmitField('Save')

class IncidentForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired()])
    camera_id = SelectField('Camera', coerce=int, validators=[Optional()])
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    severity = SelectField('Severity', choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], validators=[DataRequired()])
    status = SelectField('Status', choices=[
        ('open', 'Open'),
        ('investigating', 'Investigating'),
        ('closed', 'Closed')
    ], validators=[DataRequired()])
    submit = SubmitField('Save')
