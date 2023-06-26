from flask import Flask, render_template, request, jsonify, make_response, redirect, url_for, session
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from dns_zone import DnsZone, DnsError
from authomatic.adapters import WerkzeugAdapter
from authomatic import Authomatic
from config import CONFIG
import os

# Instantiate Authomatic.
authomatic = Authomatic(CONFIG, 'your secret string', report_errors=False)

app = Flask(__name__)
auth = HTTPBasicAuth()
app.secret_key = 'Welkom01'

users = {
    os.getenv("FLASK_APP_USERNAME"): generate_password_hash(os.getenv("FLASK_APP_PASSWORD")),
}

@auth.verify_password
def verify_password(username, password):
    if username in users and \
            check_password_hash(users.get(username), password):
        return username

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
    

@app.route('/login/<provider_name>/', defaults={'provider_name': 'google'}, methods=['GET', 'POST'])
def login(provider_name):
    response = make_response()
    result = authomatic.login(WerkzeugAdapter(request, response), provider_name)
    if result:
        if result.user:
            result.user.update()
            session['user'] = result.user.id
            return render_template('login.html', result=result)
    if result and result.user:
        if result.user.credentials:  
            return redirect(url_for('dns_page'))  
    return response

@app.route('/dns_page')
def dns_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dns.html')

@app.route('/dns', methods=['POST'])
def manage_dns():
    data = request.get_json()
    action = data.get('action')
    fqdn = data.get('fqdn')
    ipv4 = data.get('ipv4')

    zone = "net2connect.nl"
    nameserver = "192.168.1.10"
    dns_zone = DnsZone(zone, nameserver)

    try:
        if action == 'check':
            result = dns_zone.check_address(fqdn)
        elif action == 'update':
            result = dns_zone.update_address(fqdn, ipv4)
        elif action == 'clear':
            result = dns_zone.clear_address(fqdn)
        elif action == 'add':
            result = dns_zone.add_address(fqdn, ipv4)
        else:
            result = {'error': True, 'error_text': 'Invalid action'}, 400
    except DnsError as e:
        result = {'error': True, 'error_text': e.message}, e.status_code

    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True, ssl_context='adhoc', host='192.168.1.10.nip.io', port=5000)