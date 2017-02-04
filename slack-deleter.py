from flask import Flask, request, render_template
import flask_cache
from datetime import datetime
import file_deleter
import json
import requests
import os
from urllib.parse import urlencode

app = Flask(__name__)


def get_redirect_url():
    try:
        if LOCAL:
            return 'http://127.0.0.1:5000/oauth/success/'
        else:
            domain=os.environ.get('DOMAIN')
            return 'https://{}/oauth/success/'.format(domain)
    except NameError:
        domain = os.environ.get('DOMAIN')
        return 'https://{}/oauth/success/'.format(domain)


@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/token/', methods=['GET', 'POST'])
def delete():
    if request.method == 'GET':
        args = request.args.to_dict()
        keys = list(args.keys())
        if 'api_token' in keys and 'weeks' in keys:
            context = {
                'weeks': request.args.get('weeks'),
                'api_token': request.args.get('api_token')
            }
            return render_template('token-delete-success.html', **context)
        else:
            return render_template('token-delete-form.html')
    elif request.method == 'POST':
        api_token = request.form['api_token']
        weeks = int(request.form['weeks'])
        count = file_deleter.main(api_token, weeks=weeks)

        return json.dumps({'files': count})

@app.route('/oauth/', methods=['GET'])
def oauth():
    SLACK_CLIENT_ID = os.environ.get('SLACK_CLIENT_ID')
    redirect_url = get_redirect_url()
    parameters = {
        'client_id': SLACK_CLIENT_ID,
        'scope': 'files:read files:write:user',
        'redirect_uri': redirect_url,
    }
    auth_url = urlencode(parameters)
    return render_template('oauth.html', auth_url=auth_url)

@app.route('/oauth/success/', methods=['GET'])
def oauth_success():
    SLACK_CLIENT_ID = os.environ.get('SLACK_CLIENT_ID')
    SLACK_CLIENT_SECRET = os.environ.get('SLACK_CLIENT_SECRET')
    code = request.args.get('code')
    url = 'https://slack.com/api/oauth.access'
    redirect_url = get_redirect_url()
    parameters = {
        'client_id': SLACK_CLIENT_ID,
        'client_secret': SLACK_CLIENT_SECRET,
        'code': code,
        'redirectl_uri': redirect_url
    }
    response = requests.post(url,data=parameters).json()
    if response['ok'] == True and 'files:read,files:write:user' in response['scope']:
        cache.add(key=code, value=response['access_token'])
        return render_template('oauth-success-form.html', token=response['access_token'])
    elif response['ok'] == False and response['error'] == 'code_already_used':
        token = cache.get(code)
        if token:
            return render_template('oauth-success-form.html', token=token)
        else:
            return render_template('oauth-failure.html')
    else:
        print(json.dumps(response, indent=4))
        return render_template('oauth-failure.html')

@app.route('/oauth-delete/', methods=['GET'])
def oauth_delete():
    try:
        context = {
            'weeks': request.args.get('weeks'),
            'api_token': request.args.get('api_token')
        }
        return render_template('ouath-success-success.html', **context)
    except KeyError:
        return render_template('oauth-failure.html')


if __name__ == '__main__':
    LOCAL = os.environ.get('LOCAL', False)
    cache = flask_cache.Cache(app, config={
        'CACHE_TYPE': 'simple',
        'CACHE_DEFAULT_TIMEOUT': 10*60
    })
    if not LOCAL:
        app.run('0.0.0.0', 8080)
    else:
        app.run()
