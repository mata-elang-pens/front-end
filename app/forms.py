from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo
import requests, os

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    company = StringField('Company', validators=[DataRequired()])
    agree_terms = BooleanField('I Agree With The Terms and Privacy Policy')
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        url = 'http://{}/api/users/v1.0/getuserdetail/{}'.format(os.environ.get('API_HOST'), username)
        r = requests.post(url, auth=(os.environ.get('SECRET_TOKEN'), os.environ.get('SECRET_PASS')))
        if r.status_code == 200:
            raise ValidationError('Please use a different username.')

class CreateSensorForm(FlaskForm):
    device_name = StringField('Device Name', validators=[DataRequired()])
    hostname = StringField('Hostname', validators=[DataRequired()])
    ip_address = StringField('IP Address', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    protected_subnet = StringField('Protected Subnet', validators=[DataRequired()])
    submit = SubmitField('Create Sensor')