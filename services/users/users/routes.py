from urllib.parse import urljoin
from flask import request, redirect, url_for, flash, send_from_directory, render_template, abort
from flask_babel import gettext
from flask_mail import Message
import requests
from users import app, logger, redis_users, mail, captcha, db
from users.utils import is_invalid_email, generate_password_salt, calc_crypt_hash, generate_random_secret
from users.models import User


def _verify_captcha(captcha_is_required):
    """Verify captcha if required."""

    if captcha_is_required:
        captcha_response = request.form.get(app.config['CAPTCHA_RESPONSE_FIELD_NAME'], '')
        captcha_solution = captcha.verify(captcha_response, request.remote_addr)
        captcha_passed = captcha_solution.is_valid
        captcha_error_message = captcha_solution.error_message
        if not captcha_passed and captcha_error_message is None:
            captcha_error_message = gettext('Incorrect captcha solution.')
    else:
        captcha_passed = True
        captcha_error_message = None
    return captcha_passed, captcha_error_message


def _verify_recovery_code(signup_key, email, recovery_code):
    """Verify if given recovery code is correct for given email."""

    user = User.query.filter_by(email=email).one_or_none()
    if user and user.recovery_code_hash == calc_crypt_hash(user.salt, recovery_code):
        return True
    num_failures = int(redis_users.hincrby(signup_key, 'fails'))
    if num_failures >= app.config['RECOVERY_CODE_MAX_ATTEMPTS']:
        redis_users.delete(signup_key)
        abort(403)
    return False


def _create_choose_password_link(email, computer_code, new_user):
    """Return a temporary link for email verification."""

    secret = generate_random_secret()
    signup_key = 'signup:' + secret
    with redis_users.pipeline() as p:
        p.hmset(signup_key, {
            'email': email,
            'cookie': computer_code,
        })
        if new_user:
            p.hset(signup_key, 'new', '1')
        p.expire(signup_key, app.config['SIGNUP_REQUEST_EXPIRATION_SECONDS'])
        p.execute()
    return urljoin(request.host_url, url_for('choose_password', secret=secret))


def _fetch_hydra_login_request(challenge_id):
    request_url = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/login/') + challenge_id
    r = requests.get(request_url, timeout=1)
    r.raise_for_status()
    login_data = r.json()
    return request_url, login_data['subject'] if login_data['skip'] else None


def _accept_hydra_login_request(request_url, subject, remember=False, remember_for=0):
    """Approve login request, return a URL to redirect to."""

    r = requests.put(request_url + '/accept', json={
        'subject': subject,
        'remember': remember,
        'remember_for': remember_for,
    })
    r.raise_for_status()
    return r.json()['redirect_to']


def _fetch_hydra_consent_request(challenge_id):
    request_url = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/consent/') + challenge_id
    r = requests.get(request_url, timeout=1)
    r.raise_for_status()
    consent_data = r.json()
    return request_url, [] if consent_data['skip'] else consent_data['requested_scope']


def _accept_hydra_consent_request(request_url, grant_scope, remember=False, remember_for=0):
    """Approve consent request, return a URL to redirect to."""

    r = requests.put(request_url + '/accept', json={
        'grant_scope': grant_scope,
        'remember': remember,
        'remember_for': remember_for,
    })
    r.raise_for_status()
    return r.json()['redirect_to']


@app.route('/users/hello_world')
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


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    is_new_user = 'recover' not in request.args
    page_head = gettext('Create a New Account') if is_new_user else gettext('Recover Your Account')
    if request.method == 'POST':
        captcha_passed, captcha_error_message = _verify_captcha(app.config['SHOW_CAPTCHA_ON_SIGNUP'])
        email = request.form['email']
        if is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message)
        else:
            computer_code = generate_random_secret()  # to be sent to the user as a cookie
            site = app.config['SITE_TITLE']
            user = User.query.filter_by(email=email).one_or_none()
            if user:
                if is_new_user:
                    msg = Message(
                        subject=gettext('%(site)s: Duplicate registration', site=site),
                        recipients=[email],
                        body=render_template(
                            'duplicate_registration.txt',
                            email=email,
                            site=site,
                        ),
                    )
                else:
                    account_recovery_link = _create_choose_password_link(email, computer_code, new_user=False)
                    msg = Message(
                        subject=gettext('%(site)s: Please confirm your email address', site=site),
                        recipients=[email],
                        body=render_template(
                            'confirm_account_recovery.txt',
                            email=email,
                            account_recovery_link=account_recovery_link,
                        ),
                    )
                mail.send(msg)
            elif is_new_user:
                register_link = _create_choose_password_link(email, computer_code, new_user=True)
                msg = Message(
                    subject=gettext('%(site)s: Please confirm your registration', site=site),
                    recipients=[email],
                    body=render_template(
                        'confirm_registration.txt',
                        email=email,
                        register_link=register_link,
                    ),
                )
                mail.send(msg)
            response = redirect(url_for('report_sent_signup_email', email=email))
            response.set_cookie(app.config['COMPUTER_CODE_COOKE_NAME'], computer_code)
            return response

    return render_template('signup.html', page_head=page_head, display_captcha=captcha.display_html)


@app.route('/signup/email')
def report_sent_signup_email():
    email = request.args['email']
    return render_template('report_sent_signup_email.html', email=email)


@app.route('/password/<secret>', methods=['GET', 'POST'])
def choose_password(secret):
    signup_key = 'signup:' + secret
    email, cookie, is_new_user = redis_users.hmget(signup_key, ['email', 'cookie', 'new'])
    if email is None:
        abort(404)  # invalid registration link
    require_recovery_code = not is_new_user and app.config['USE_RECOVERY_CODE']

    if request.method == 'POST':
        recovery_code = request.form.get('recovery_code', '')
        password = request.form['password']
        min_length = app.config['PASSWORD_MIN_LENGTH']
        max_length = app.config['PASSWORD_MAX_LENGTH']
        if len(password) < min_length:
            flash(gettext('The password should have least %(num)s characters.', num=min_length))
        elif len(password) > max_length:
            flash(gettext('The password should have at most %(num)s characters.', num=max_length))
        elif password != request.form['confirm']:
            flash(gettext('Passwords do not match.'))
        elif require_recovery_code and not _verify_recovery_code(signup_key, email, recovery_code):
            flash(gettext('Incorrect recovery code.'))
        else:
            redis_users.delete(signup_key)
            if is_new_user:
                salt = generate_password_salt(app.config['PASSWORD_HASHING_METHOD'])
                recovery_code = generate_random_secret()
                user = User(
                    email=email,
                    salt=salt,
                    password_hash=calc_crypt_hash(salt, password),
                    recovery_code_hash=calc_crypt_hash(salt, recovery_code),
                )
                db.session.add(user)
                response = recovery_code
            else:
                user = User.query.filter_by(email=email).one()
                user.password_hash = calc_crypt_hash(user.salt, password)
                response = 'ok'
            db.session.commit()
            redis_users.zadd('cc:' + str(user.user_id), 1, cookie)  # TODO: use a function
            return response

    return render_template('choose_password.html', require_recovery_code=require_recovery_code)


@app.route('/signup/success')
def report_signup_success():
    return "/signup/success"


@app.route('/login', methods=['GET', 'POST'])
def login():
    request_url, subject = _fetch_hydra_login_request(request.args['login_challenge'])
    if subject:
        # Hydra says the user is logged in already.
        return redirect(_accept_hydra_login_request(request_url, subject))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).one_or_none()
        if user and user.password_hash == calc_crypt_hash(user.salt, password):
            subject = 'user:{}'.format(user.user_id)
            return redirect(_accept_hydra_login_request(request_url, subject))
        flash(gettext('Incorrect email or password.'))

    return render_template('login.html')


@app.route('/login/verification-code')
def enter_verification_code():
    return "/login/verification-code"


@app.route('/consent', methods=['GET', 'POST'])
def consent():
    request_url, requested_scopes = _fetch_hydra_consent_request(request.args['consent_challenge'])
    if not requested_scopes:
        # Hydra says all requested scopes are granted already.
        return redirect(_accept_hydra_consent_request(request_url, requested_scopes))

    # TODO: show UI.
    return redirect(_accept_hydra_consent_request(request_url, requested_scopes))
