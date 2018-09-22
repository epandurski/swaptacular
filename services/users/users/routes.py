from flask import request, redirect, url_for, flash, send_from_directory, render_template
from flask_babel import gettext
from users import app, logger, redis_users
from users.utils import is_invalid_email


@app.route('/users/')
def hello_world():
    logger.debug('A debug message')
    logger.info('An info message')
    logger.warning('A warning message')
    body = app.config['MESSAGE'] + '\n\n' + '\n'.join('{}: {}'.format(*h) for h in request.headers)
    return body, 200, {'Content-Type': 'text/plain; charset=utf-8'}


@app.route('/users/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)


@app.route('/users/language/<lang>')
def set_language(lang):
    response = redirect(request.args['to'])
    response.set_cookie(app.config['LANGUAGE_COOKE_NAME'], lang)
    return response


@app.route('/users/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        is_valid = False
        password_length = len(request.form['password'])
        min_length, max_length = app.config['PASSWORD_MIN_LENGTH'], app.config['PASSWORD_MAX_LENGTH']
        if is_invalid_email(request.form['email']):
            flash(gettext('The email address is invalid.'))
        elif password_length < min_length:
            flash(gettext('The password should have least %(num)s characters.', num=min_length))
        elif password_length > max_length:
            flash(gettext('The password should have at most %(num)s characters.', num=max_length))
        elif request.form['password'] != request.form['confirm']:
            flash(gettext('Passwords do not match.'))
        else:
            is_valid = True
        if is_valid:
            redis_users.set('message', 'OK')
            return redirect(url_for('report_sent_signup_email', email=request.form['email']))
    return render_template('signup.html')


@app.route('/users/signup/email')
def report_sent_signup_email():
    email = request.args['email']
    return render_template('report_sent_signup_email.html', email=email)


@app.route('/users/signup/success/<secret>')
def report_signup_success(secret):
    return "/users/signup/success/{}".format(secret)


@app.route('/users/login')
def login():
    challenge = request.args['login_challenge']
    return render_template('login.html')


@app.route('/users/login/verification-code')
def enter_verification_code():
    return "/login/code"


@app.route('/users/recover-password')
def recover_password():
    return "/users/recover-password"


@app.route('/users/recover-password/email')
def report_sent_recover_password_email():
    return "/users/recover-password/email"


@app.route('/users/choose-password/<secret>')
def choose_password(secret):
    return "/users/choose-password/{}".format(secret)


@app.route('/users/choose-password/success')
def report_choose_password_success():
    return "/users/choose-password/success"
