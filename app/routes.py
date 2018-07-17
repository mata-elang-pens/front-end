from flask import render_template, flash, redirect, url_for, session, request
from flask_login import current_user, login_user, logout_user, login_required
from app import app
from app.forms import LoginForm, RegistrationForm, CreateSensorForm
from app.models import User
from datetime import datetime
import requests, json, os

@app.route('/')
@app.route('/index')
@login_required
def index():
    breadcrumb = [
        {'page' : 'Dashboard', 'link' : 'index'},
        {'page' : 'Sensor List', 'link' : 'index'}
    ]
    hitPerDay = "0"
    url = 'http://{}/api/sensors/v1.0/listsensors'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"))
    data = json.loads(r.text)
    for i in range(len(data['sensors'])):
        #Check per sensors
        data['sensors'][i]['status'] = "running" 

    return render_template('index.html', title="Sensor List", breadcrumb=breadcrumb, sensors=data['sensors'], company=data['company'], numSensor=data['count'], hitPerDay=hitPerDay)

@app.route('/index/createsensor', methods=['GET', 'POST'])
@login_required
def createsensor():
    breadcrumb = [
        {'page' : 'Dashboard', 'link' : 'index'},
        {'page' : 'Sensor List', 'link' : 'index'},
        {'page' : 'Create Sensor', 'link': 'createsensor'}
    ]
    form = CreateSensorForm()
    if form.validate_on_submit():
        device_name = form.device_name.data
        hostname = form.hostname.data
        ip_address = form.ip_address.data
        location = form.location.data
        protected_subnet = form.protected_subnet.data
        payload = {
            "device_name" : device_name,
            "hostname" : hostname,
            "ip_address" : ip_address,
            "location" : location,
            "protected_subnet" : protected_subnet
        }
        headers = {
            'content-type': 'application/json'
        }
        url = 'http://{}/api/sensors/v1.0/createsensor'.format(os.environ.get('API_HOST'))
        r = requests.post(url, data=json.dumps(payload), headers=headers, auth=(session['token'], "pass"))
        if r.status_code == 200:
            flash('Sensor Created Successfully')
            return redirect(url_for('index'))
        else:
            flash('Error Creating Sensor')
            return redirect(url_for('createsensor'))
    
    return render_template('createsensor.html', title='Create Sensor | Kaspa', form=form, breadcrumb=breadcrumb)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username=form.username.data
        password=form.password.data
        urlToken = 'http://{}/api/token/v1.0/getauthtoken'.format(os.environ.get('API_HOST'))
        r_token = requests.post(urlToken, auth=(username, password))
        if r_token.status_code == 200:
            token = (json.loads(r_token.text))['token']
            session['token'] = token
        else:
            print("salah")
            flash('Invalid username or password')
            return redirect(url_for('login'))

        url = 'http://{}/api/users/v1.0/getuserdetail/{}'.format(os.environ.get('API_HOST'), username)
        r = requests.post(url, auth=(token, "pass"))
        data = json.loads(r.text)
        #data contain : username, first_name, last_name, email, company
        user = User(data['username'], data['first_name'], data['last_name'], data['email'], data['company'])
        login_user(user, remember=form.remember_me.data)
        return redirect(url_for('index'))

    return render_template('login.html', title='Sign In | Kaspa', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit() and form.agree_terms.data:
        username = form.username.data
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        company = form.company.data

        url = 'http://{}/api/users/v1.0/createuser'
        payload = {
            "username" : username,
            "password" : password,
            "first_name" : first_name,
            "last_name" : last_name,
            "email" : email,
            "company" : company
        }
        headers = {
            'content-type': 'application/json'
        }
        r = requests.post(url, data=json.dumps(payload), headers=headers, auth=(os.environ.get('API_USER'), os.environ.get('API_PASS')))
        if r.status_code == 200:
            flash('Registration Success!!')
            return redirect(url_for('login'))
    return render_template('register.html', title='Sign Up | Kaspa', form=form)

@app.route('/monitoring/events', methods=['GET', 'POST'])
@login_required
def events():
    breadcrumb = [
        {'page': 'Monitoring', 'link' : 'events' },
        {'page': 'Events', 'link' : 'events'}
    ]
    payload = {
        "company" : "IDSIRTII",
        "limit" : "500"
    }
    headers = {
        'content-type': 'application/json'
    }

    url = 'http://{}/api/statistic/v1.0/rawdata'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data = json.loads(r.text)

    if r.status_code == 200:
        flash('Event data parsed successfully')
    else:
        flash('Error Occured')

    for i in range(len(data['data'])):
        #Check per sensors
        data['data'][i]['date_time'] = datetime(data['data'][i]['year'],
                                                data['data'][i]['month'],
                                                data['data'][i]['day'],
                                                data['data'][i]['hour'],
                                                data['data'][i]['minute'],
                                                data['data'][i]['second'])

    return render_template('events.html', title='Raw Events', breadcrumb=breadcrumb, events=data['data'], company=data['company'], count=data['count'])

@app.route('/monitoring/event_hit', methods=['GET', 'POST'])
@login_required
def event_hit_parent():
    breadcrumb = [
        {'page': 'Monitoring', 'link' : 'event_hit_parent' },
        {'page': 'Event Hit', 'link' : 'event_hit_parent'}
    ]

    url = 'http://{}/api/sensors/v1.0/listsensors'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"))
    data = json.loads(r.text)
    for i in range(len(data['sensors'])):
        #Check per sensors
        data['sensors'][i]['color'] = i % 4
        data['sensors'][i]['daily_hit'] = str(0)

    return render_template('event_hit.html', title="Event Hit", breadcrumb=breadcrumb, sensors=data['sensors'], company=data['company'], today=datetime.now().date())


@app.route('/monitoring/events_hit/<device_id>/<granularity>', methods=['GET', 'POST'])
@login_required
def event_hit(device_id, granularity):
    breadcrumb = [
        {'page': 'Monitoring', 'link' : 'events' },
        {'page': 'Events Hit', 'link' : 'eventshit'},
        {'page': '{}'.format(granularity), 'link' : 'eventshit({})'.format(granularity)}
    ]
    payload = {
        "company" : "IDSIRTII",
        "limit" : "2000"
    }
    if granularity == "second":
        payload = {
            "company" : "IDSIRTII",
            "limit" : "500"
        }
        print("Second")
    elif granularity == "minute":
        print("Minute")
    elif granularity == "hourly":
        print("Hourly")
    elif granularity == "daily":
        print("Daily")
    elif granularity == "monthly":
        print("Monthly")
    elif granularity == "annually":
        print("Annually")
    
    headers = {
        'content-type': 'application/json'
    }

    url = 'http://{}/api/statistic/v1.0/rawdata'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data = json.loads(r.text)


@app.route('/logout')
def logout():
    logout_user()
    session.pop('token', None)
    return redirect(url_for('index'))