from app import login
from flask_login import UserMixin
import requests, os, json

class User(UserMixin, object):
    def __init__(self, username, first_name, last_name, email, company):
        self.username = username
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.company = company
    
    def get_id(self):
        return self.username


@login.user_loader
def load_user(username):
    url = 'http://{}/api/users/v1.0/getuserdetail/{}'.format(os.environ.get('API_HOST'), username)
    r = requests.post(url, auth=(os.environ.get('API_USER'), os.environ.get('API_PASS')))
    if r.status_code != 200:
        return None

    data = json.loads(r.text)
    user = User(data['username'], data['first_name'], data['last_name'], data['email'], data['company'])
    return user

        
