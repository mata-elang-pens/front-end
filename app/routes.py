from flask import render_template, flash, redirect, url_for, session, request
from flask_login import current_user, login_user, logout_user, login_required
from app import app
from app.forms import LoginForm, RegistrationForm, CreateSensorForm
from app.models import User
from datetime import datetime
from random import randint
import requests, json, os

@app.route('/')
@app.route('/index')
@login_required
def index():
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    hour = datetime.now().hour
    minute = datetime.now().minute
    second = datetime.now().second

    hitPerHour = 0

    headers = {
        'content-type': 'application/json'
    }

    breadcrumb = [
        {'page' : 'Dashboard', 'link' : 'index'},
        {'page' : 'Sensor List', 'link' : 'index'}
    ]

    url = 'http://{}/api/sensors/v1.0/listsensors'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"))
    data = json.loads(r.text)

    payloadHit = {
        "company" : data['company'],
        "year" : year,
        "month" : month,
        "day" : day,
        "limit" : "100"
    }
    url_hit = 'http://{}/api/statistic/v1.0/eventhit'.format(os.environ.get('API_HOST'))
    r_hit = requests.post(url_hit, auth=(session['token'], "pass"), data=json.dumps(payloadHit), headers=headers)
    print("Status Code : {}".format(r_hit.status_code))
    data_hit = json.loads(r_hit.text)

    for item in data_hit['data']:
        if item['hour'] == hour:
            hitPerHour = item['value']

    for i in range(len(data['sensors'])):
        #Check per sensors
        data['sensors'][i]['status'] = "running" 

    return render_template(
        'index.html', 
        title="Sensor List", 
        breadcrumb=breadcrumb, 
        sensors=data['sensors'], 
        company=data['company'], 
        numSensor=data['count'], 
        hitPerHour=hitPerHour
    )

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
    
    return render_template(
        'createsensor.html', 
        title='Create Sensor | Kaspa', 
        form=form, 
        breadcrumb=breadcrumb
    )

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

    return render_template(
        'login.html', 
        title='Sign In | Kaspa', 
        form=form
    )

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
    return render_template(
        'register.html', 
        title='Sign Up | Kaspa', 
        form=form
    )

@app.route('/monitoring/events', methods=['GET', 'POST'])
@login_required
def events():
    breadcrumb = [
        {'page': 'Monitoring', 'link' : 'events' },
        {'page': 'Events', 'link' : 'events'}
    ]
    payload = {
        "company" : "{}".format(current_user.company),
        "limit" : "1000"
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

    return render_template(
        'events.html', 
        title='Raw Events', 
        breadcrumb=breadcrumb, 
        events=data['data'], 
        company=data['company'], 
        count=data['count']
    )

@app.route('/monitoring/event_hit', methods=['GET', 'POST'])
@login_required
def event_hit_parent():
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    hour = datetime.now().hour
    minute = datetime.now().minute
    second = datetime.now().second

    breadcrumb = [
        {'page': 'Monitoring', 'link' : 'event_hit_parent' },
        {'page': 'Event Hit', 'link' : 'event_hit_parent'}
    ]
    headers = {
        'content-type': 'application/json'
    }

    url = 'http://{}/api/sensors/v1.0/listsensors'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"))
    data = json.loads(r.text)
    for i in range(len(data['sensors'])):
        #Check per sensors
        data['sensors'][i]['color'] = i % 4
        data['sensors'][i]['daily_hit'] = str(0)
        payload = {
            "year" : year,
            "month" : month,
            "day" : day,
            "limit" : 100
        }
        
        url = 'http://{}/api/statistic/v1.0/eventhit/{}'.format(os.environ.get('API_HOST'), data['sensors'][i]['device_id'])
        r = requests.post(url, data=json.dumps(payload), headers=headers, auth=(session['token'], "pass"))
        data_hit = json.loads(r.text)
        for j in data_hit['data']:
            if j['hour'] == hour:
                data['sensors'][i]['daily_hit'] = str(j['value'])
    

    payload = {
        "company" : data['company'],
        "year" : year,
        "month" : month,
        "day" : day,
        "limit" : "100"
    }
    labels_hour = [ i+1 for i in range(24) ]
    values = [ 0 for i in range(24) ]

    url_hit = 'http://{}/api/statistic/v1.0/eventhit'.format(os.environ.get('API_HOST'))
    r_hit = requests.post(url_hit, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    print("Status Code : {}".format(r_hit.status_code))
    data_hit = json.loads(r_hit.text)

    for item in data_hit['data']:
        values[item['hour']] = item['value']
    
    return render_template(
        'event_hit.html', 
        title="Event Hit", 
        breadcrumb=breadcrumb, 
        sensors=data['sensors'], 
        company=data['company'],
        labels=labels_hour,
        values=values,
        today=datetime.now().date()
    )

@app.route('/monitoring/events_hit/<device_id>/<granularity>', methods=['GET', 'POST'])
@login_required
def event_hit(device_id, granularity):
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day
    hour = datetime.now().hour
    minute = datetime.now().minute

    breadcrumb = [
        {'page': 'Monitoring', 'link' : 'events' },
        {'page': 'Events Hit', 'link' : 'event_hit_parent'},
        {'page': '{}'.format(device_id), 'link' : 'event_hit_parent'},
        {'page': '{}'.format(granularity), 'link' : 'event_hit'}
    ]
    payload = {
        "device_id" : device_id,
        "limit" : "2000"
    }
    headers = {
        'content-type': 'application/json'
    }
    url = 'http://{}/api/statistic/v1.0/eventhit/{}'.format(os.environ.get('API_HOST'), device_id)

    if granularity == "annually":
        l = [ datetime.now().year - i for i in range(5)]
        label = l[::-1]
        value = [ 0 for i in range(5)]
    elif granularity == "monthly":
        if request.method == 'POST':
            if request.form.get('year', None):
                year = request.form['year']
        payload['year'] = year
        label = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
        value = [ 0 for i in range(12)]
    elif granularity == "daily":
        if request.method == 'POST':
            if request.form.get('year-month', None):
                parsed = datetime.strptime(request.form['year-month'], '%Y-%m')
                year = parsed.year
                month = parsed.month
        payload['year'] = year
        payload['month'] = month
        label = [ i+1 for i in range(31)]
        value = [ 0 for i in range(31)]
    elif granularity == "hourly":
        if request.method == 'POST':
            if request.form.get('year-month-day', None):
                print(request.form['year-month-day'])
                parsed = datetime.strptime(request.form['year-month-day'], '%Y-%m-%d')
                year = parsed.year
                month = parsed.month
                day = parsed.day
        payload['year'] = year
        payload['month'] = month
        payload['day'] = day
        label = [ i for i in range(24)]
        value = [ 0 for i in range(24)]
    elif granularity == "minute":
        if request.method == 'POST':
            if request.form.get('datetime', None):
                parsed = datetime.strptime(request.form['datetime'], '%Y-%m-%dT%I:%M')
                year = parsed.year
                month = parsed.month
                day = parsed.day
                hour = parsed.hour
        payload['year'] = year
        payload['month'] = month
        payload['day'] = day
        payload['hour'] = hour
        label = [ i for i in range(60) ]
        value = [ 0 for i in range(60)]
    else:
        return redirect(url_for('event_hit_parent'))

    headers = {
        'content-type': 'application/json'
    }

    r = requests.post(url, data=json.dumps(payload), headers=headers, auth=(session['token'], "pass"))
    data = json.loads(r.text)
    hit = data['data']
    print(hit)

    if granularity == "annually":
        for item in hit:
            value[datetime.now().year - item['year']] = item['value']
        value = value[::-1]
    elif granularity == "monthly":
        for item in hit:
            value[item['month'] - 1] = item['value']
    elif granularity == "daily":
        for item in hit:
            value[item['day'] - 1] = item['value']
    elif granularity == "hourly":
        for item in hit:
            value[item['hour']] = item['value'] 
    elif granularity == "minute":        
        for item in hit:
            value[item['minute']] = item['value']
        

    payload_event = {
        "device_id" : device_id,
        "limit" : "500"
    }
    url = 'http://{}/api/statistic/v1.0/rawdata/{}'.format(os.environ.get('API_HOST'), device_id)
    r = requests.post(url, auth=(session['token'], "pass"), data=json.dumps(payload_event), headers=headers)
    data_event = json.loads(r.text)
    for i in range(len(data_event['data'])):
        #Check per sensors
        data_event['data'][i]['date_time'] = datetime(data_event['data'][i]['year'],
                                                data_event['data'][i]['month'],
                                                data_event['data'][i]['day'],
                                                data_event['data'][i]['hour'],
                                                data_event['data'][i]['minute'],
                                                data_event['data'][i]['second'])

    return render_template(
        'event_hit_device.html',
        title="Event Hit On Device", 
        breadcrumb=breadcrumb, 
        device_id=device_id,
        labels=label,
        values=value,
        granularity=granularity,
        data_event=data_event['data'],
        today=datetime.now().date(),
        curyear=datetime.now().year,
        curmonth=datetime.now().month,
        curday=datetime.now().day,
        curhour=datetime.now().hour,
        curmin=datetime.now().minute,
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute
    )

@app.route('/monitoring/event_sensor', methods=['GET', 'POST'])
@login_required
def event_sensor():
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day

    breadcrumb = [
        {'page': 'Monitoring', 'link' : 'event_sensor' },
        {'page': 'Sensor Statistic', 'link' : 'event_sensor'}
    ]
    label_hour = [ i for i in range(24)]
    datasets = []

    headers = {
        'content-type': 'application/json'
    }
    
    url = 'http://{}/api/sensors/v1.0/listsensors'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"))
    data = json.loads(r.text)
    for sensor in data['sensors']:
        #Check per sensors
        payload = {
            "device_id" : sensor['device_id'],
            "year" : year,
            "month" : month,
            "day" : day,
            "limit" : "100"
        }
        dataset = {
            "label" : sensor['device_id'],
            "data" : [ 0 for i in range(24)],
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }

        url_hit = 'http://{}/api/statistic/v1.0/eventhit/{}'.format(os.environ.get('API_HOST'), sensor['device_id'])
        r_hit = requests.post(url_hit, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
        data_hit = json.loads(r_hit.text)

        for item in data_hit['data']:
            dataset['data'][item['hour']] = item['value']
        
        datasets.append(dataset)

    return render_template(
        'sensor_statistic.html', 
        title="Sensor Statistic", 
        breadcrumb=breadcrumb, 
        datasets=datasets, 
        label_hour=label_hour,
        today=datetime.now().date()
    )

@app.route('/monitoring/top_signature', methods=['GET', 'POST'])
@login_required
def top_signature():
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day - 1

    breadcrumb = [
        {'page' : 'Monitoring', 'link' : 'top_signature'},
        {'page' : 'Top Signature', 'link' : 'top_signature'}
    ]

    payload={
        "company" : "{}".format(current_user.company),
        "year" : year,
        "month" : month,
        "day" : day,
        "limit" : 1000
    }

    headers = {
        'content-type': 'application/json'
    }

    url = 'http://{}/api/statistic/v1.0/signaturehit'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data = json.loads(r.text)
    top = sorted(data['data'], key=lambda count: count['value'], reverse=True)[:20]

    labels = []
    values = []
    colors = []
    for sign in top:
        labels.append(sign['alert_msg'])
        values.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors.append(col)
    

    return render_template(
        'top_signature.html',
        title='Top 20 Signature Hit',
        breadcrumb=breadcrumb,
        top_signature=top,
        company=data['company'],
        labels=labels,
        values=values,
        colors=colors,
        today = datetime.now().date()
    )

@app.route('/monitoring/top_protocol', methods=['GET', 'POST'])
@login_required
def top_protocol():
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day - 1

    breadcrumb = [
        {'page' : 'Monitoring', 'link' : 'top_protocol'},
        {'page' : 'Top Protocol', 'link' : 'top_protocol'}
    ]

    payload={
        "company" : "{}".format(current_user.company),
        "year" : year,
        "month" : month,
        "day" : day,
        "limit" : 1000
    }

    headers = {
        'content-type': 'application/json'
    }

    url = 'http://{}/api/statistic/v1.0/protocolhit'.format(os.environ.get('API_HOST'))
    r = requests.post(url, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data = json.loads(r.text)
    top = sorted(data['data'], key=lambda count: count['value'], reverse=True)

    labels = []
    values = []
    colors = []
    for protocol in top:
        labels.append(protocol['protocol'])
        values.append(protocol['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors.append(col)
    

    return render_template(
        'top_protocol.html',
        title='Top 20 Protocol Hit',
        breadcrumb=breadcrumb,
        top_protocol=top[:20],
        company=data['company'],
        labels=labels,
        values=values,
        colors=colors,
        today = datetime.now().date()
    )

@app.route('/monitoring/top_protocol/<protocol>', methods=['GET', 'POST'])
@login_required
def top_protocol_spec(protocol):
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day - 1
    prot = protocol

    breadcrumb = [
        {'page' : 'Monitoring', 'link' : 'top_protocol'},
        {'page' : 'Top Protocol : {}'.format(protocol), 'link' : 'top_protocol'}
    ]

    payload={
        "company" : "{}".format(current_user.company),
        "year" : year,
        "month" : month,
        "day" : day,
        "limit" : 1000
    }

    headers = {
        'content-type': 'application/json'
    }

    url = 'http://{}/api/statistic/v1.0/protocolbysporthit/{}'.format(os.environ.get('API_HOST'), protocol)
    r = requests.post(url, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data = json.loads(r.text)
    top = sorted(data['data'], key=lambda count: count['value'], reverse=True)

    labels = []
    values = []
    colors = []
    for protocol in top[:20]:
        labels.append(protocol['src_port'])
        values.append(protocol['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors.append(col)

    return render_template(
        'top_protocol_spec.html',
        title='Top 20 Port Source by Protocol',
        breadcrumb=breadcrumb,
        top_protocol=top[:20],
        protocol=prot,
        company=data['company'],
        labels=labels,
        values=values,
        colors=colors,
        today = datetime.now().date()
    )

@app.route('/report/daily', methods=['GET', 'POST'])
@login_required
def report_daily():
    year = datetime.now().year
    month = datetime.now().month
    day = datetime.now().day - 1

    breadcrumb = [
        {'page' : 'Report', 'link' : 'report_daily'},
        {'page' : 'Daily Report', 'link' : 'report_daily'}
    ]

    payload={
        "company" : "{}".format(current_user.company),
        "year" : year,
        "month" : month,
        "day" : day,
        "limit" : 1000
    }

    headers = {
        'content-type': 'application/json'
    }

    url_signature = 'http://{}/api/statistic/v1.0/signaturehit'.format(os.environ.get('API_HOST'))
    url_ip_source = 'http://{}/api/statistic/v1.0/ipsourcehit'.format(os.environ.get('API_HOST'))
    url_ip_dest = 'http://{}/api/statistic/v1.0/ipdesthit'.format(os.environ.get('API_HOST'))

    r_signature = requests.post(url_signature, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_signature = json.loads(r_signature.text)
    top_signature = sorted(data_signature['data'], key=lambda count: count['value'], reverse=True)[:20]

    r_ip_source = requests.post(url_ip_source, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_ip_source = json.loads(r_ip_source.text)
    top_ip_source = sorted(data_ip_source['data'], key=lambda count: count['value'], reverse=True)[:20]

    r_ip_dest = requests.post(url_ip_dest, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_ip_dest = json.loads(r_ip_dest.text)
    top_ip_dest = sorted(data_ip_dest['data'], key=lambda count: count['value'], reverse=True)[:20]

    labels_signature = []
    values_signature = []
    colors_signature = []
    for sign in top_signature:
        labels_signature.append(sign['alert_msg'])
        values_signature.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_signature.append(col)

    labels_ip_source = []
    values_ip_source = []
    colors_ip_source = []
    for sign in top_ip_source:
        labels_ip_source.append(sign['src_ip'])
        values_ip_source.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_ip_source.append(col)
    
    labels_ip_dest = []
    values_ip_dest = []
    colors_ip_dest = []
    for sign in top_ip_dest:
        labels_ip_dest.append(sign['dest_ip'])
        values_ip_dest.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_ip_dest.append(col)

    return render_template(
        'daily_report.html',
        title='Daily Report',
        breadcrumb=breadcrumb,
        top_signature=top_signature,
        top_ip_source=top_ip_source,
        top_ip_dest=top_ip_dest,
        company=current_user.company,
        labels_signature=labels_signature,
        labels_ip_source=labels_ip_source,
        labels_ip_dest=labels_ip_dest,
        colors_signature=colors_signature,
        colors_ip_source=colors_ip_source,
        colors_ip_dest=colors_ip_dest,
        values_signature=values_signature,
        values_ip_source=values_ip_source,
        values_ip_dest=values_ip_dest,
        today=datetime.now().date()
    )
    
@app.route('/report/monthly', methods=['GET', 'POST'])
@login_required
def report_monthly():
    year = datetime.now().year
    month = datetime.now().month

    breadcrumb = [
        {'page' : 'Report', 'link' : 'report_monthly'},
        {'page' : 'Monthly Report', 'link' : 'report_monthly'}
    ]

    payload={
        "company" : "{}".format(current_user.company),
        "year" : year,
        "month" : month,
        "limit" : 1000
    }

    headers = {
        'content-type': 'application/json'
    }

    url_signature = 'http://{}/api/statistic/v1.0/signaturehit'.format(os.environ.get('API_HOST'))
    url_ip_source = 'http://{}/api/statistic/v1.0/ipsourcehit'.format(os.environ.get('API_HOST'))
    url_ip_dest = 'http://{}/api/statistic/v1.0/ipdesthit'.format(os.environ.get('API_HOST'))

    r_signature = requests.post(url_signature, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_signature = json.loads(r_signature.text)
    top_signature = sorted(data_signature['data'], key=lambda count: count['value'], reverse=True)[:20]

    r_ip_source = requests.post(url_ip_source, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_ip_source = json.loads(r_ip_source.text)
    top_ip_source = sorted(data_ip_source['data'], key=lambda count: count['value'], reverse=True)[:20]

    r_ip_dest = requests.post(url_ip_dest, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_ip_dest = json.loads(r_ip_dest.text)
    top_ip_dest = sorted(data_ip_dest['data'], key=lambda count: count['value'], reverse=True)[:20]

    labels_signature = []
    values_signature = []
    colors_signature = []
    for sign in top_signature:
        labels_signature.append(sign['alert_msg'])
        values_signature.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_signature.append(col)

    labels_ip_source = []
    values_ip_source = []
    colors_ip_source = []
    for sign in top_ip_source:
        labels_ip_source.append(sign['src_ip'])
        values_ip_source.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_ip_source.append(col)
    
    labels_ip_dest = []
    values_ip_dest = []
    colors_ip_dest = []
    for sign in top_ip_dest:
        labels_ip_dest.append(sign['dest_ip'])
        values_ip_dest.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_ip_dest.append(col)

    return render_template(
        'monthly_report.html',
        title='Monthly Report',
        breadcrumb=breadcrumb,
        top_signature=top_signature,
        top_ip_source=top_ip_source,
        top_ip_dest=top_ip_dest,
        company=current_user.company,
        labels_signature=labels_signature,
        labels_ip_source=labels_ip_source,
        labels_ip_dest=labels_ip_dest,
        colors_signature=colors_signature,
        colors_ip_source=colors_ip_source,
        colors_ip_dest=colors_ip_dest,
        values_signature=values_signature,
        values_ip_source=values_ip_source,
        values_ip_dest=values_ip_dest,
        today="{}-{}".format(year, month)
    )
    
@app.route('/report/annually', methods=['GET', 'POST'])
@login_required
def report_annually():
    year = datetime.now().year
    month = datetime.now().month

    breadcrumb = [
        {'page' : 'Report', 'link' : 'report_annually'},
        {'page' : 'Annually Report', 'link' : 'report_annually'}
    ]

    payload={
        "company" : "{}".format(current_user.company),
        "year" : year,
        "limit" : 1000
    }

    headers = {
        'content-type': 'application/json'
    }

    url_signature = 'http://{}/api/statistic/v1.0/signaturehit'.format(os.environ.get('API_HOST'))
    url_ip_source = 'http://{}/api/statistic/v1.0/ipsourcehit'.format(os.environ.get('API_HOST'))
    url_ip_dest = 'http://{}/api/statistic/v1.0/ipdesthit'.format(os.environ.get('API_HOST'))

    r_signature = requests.post(url_signature, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_signature = json.loads(r_signature.text)
    top_signature = sorted(data_signature['data'], key=lambda count: count['value'], reverse=True)[:20]

    r_ip_source = requests.post(url_ip_source, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_ip_source = json.loads(r_ip_source.text)
    top_ip_source = sorted(data_ip_source['data'], key=lambda count: count['value'], reverse=True)[:20]

    r_ip_dest = requests.post(url_ip_dest, auth=(session['token'], "pass"), data=json.dumps(payload), headers=headers)
    data_ip_dest = json.loads(r_ip_dest.text)
    top_ip_dest = sorted(data_ip_dest['data'], key=lambda count: count['value'], reverse=True)[:20]

    labels_signature = []
    values_signature = []
    colors_signature = []
    for sign in top_signature:
        labels_signature.append(sign['alert_msg'])
        values_signature.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_signature.append(col)

    labels_ip_source = []
    values_ip_source = []
    colors_ip_source = []
    for sign in top_ip_source:
        labels_ip_source.append(sign['src_ip'])
        values_ip_source.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_ip_source.append(col)
    
    labels_ip_dest = []
    values_ip_dest = []
    colors_ip_dest = []
    for sign in top_ip_dest:
        labels_ip_dest.append(sign['dest_ip'])
        values_ip_dest.append(sign['value'])
        col = {
            "R" : randint(0,255),
            "G" : randint(0,255),
            "B" : randint(0,255)
        }
        colors_ip_dest.append(col)

    return render_template(
        'annually_report.html',
        title='Annually Report',
        breadcrumb=breadcrumb,
        top_signature=top_signature,
        top_ip_source=top_ip_source,
        top_ip_dest=top_ip_dest,
        company=current_user.company,
        labels_signature=labels_signature,
        labels_ip_source=labels_ip_source,
        labels_ip_dest=labels_ip_dest,
        colors_signature=colors_signature,
        colors_ip_source=colors_ip_source,
        colors_ip_dest=colors_ip_dest,
        values_signature=values_signature,
        values_ip_source=values_ip_source,
        values_ip_dest=values_ip_dest,
        today="{}".format(year)
    )

@app.route('/logout')
def logout():
    logout_user()
    session.pop('token', None)
    return redirect(url_for('index'))