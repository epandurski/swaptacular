from urllib.parse import urljoin
from flask import request, redirect, url_for, flash, send_from_directory, render_template, abort
from flask_babel import gettext
import requests
from users import app, logger, redis_users, db
from users import captcha
from users import emails
from users.utils import is_invalid_email, generate_password_salt, calc_crypt_hash, generate_random_secret
from users.models import User


def verify_captcha(captcha_is_required):
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


def create_login_verification_code(secret, user_id, login_challenge_id):
    vcode_key = 'vcode:' + secret
    verification_code = generate_random_secret(5)
    with redis_users.pipeline() as p:
        p.hmset(vcode_key, {
            'id': user_id,
            'code': verification_code,
            'chal': login_challenge_id,
        })
        p.expire(vcode_key, app.config['LOGIN_VERIFICATION_CODE_EXPIRATION_SECONDS'])
        p.execute()
    return verification_code


class SignUpRequest:
    REDIS_PREFIX = 'signup:'
    ENTRIES = ['email', 'cc', 'recover']

    @property
    def key(self):
        return self.REDIS_PREFIX + self.secret

    @classmethod
    def create(cls, **data):
        instance = cls()
        instance.secret = generate_random_secret()
        instance._data = data
        with redis_users.pipeline() as p:
            p.hmset(instance.key, data)
            p.expire(instance.key, app.config['SIGNUP_REQUEST_EXPIRATION_SECONDS'])
            p.execute()
        return instance

    @classmethod
    def from_secret(cls, secret):
        instance = cls()
        instance.secret = secret
        instance._data = dict(zip(cls.ENTRIES, redis_users.hmget(instance.key, cls.ENTRIES)))
        return instance if instance._data.get('email') is not None else None

    def __getattr__(self, name):
        return self._data[name]

    def _register_recovery_code_failure(self):
        num_failures = int(redis_users.hincrby(self.key, 'fails'))
        if num_failures >= app.config['RECOVERY_CODE_MAX_ATTEMPTS']:
            self._delete_from_redis()
            abort(403)

    def _delete_from_redis(self):
        redis_users.delete(self.key)

    def get_link(self):
        return urljoin(request.host_url, url_for('choose_password', secret=self.secret))

    def verify_recovery_code(self, recovery_code):
        user = User.query.filter_by(email=self.email).one_or_none()
        if user and user.recovery_code_hash == calc_crypt_hash(user.salt, recovery_code):
            return True
        self._register_recovery_code_failure()
        return False

    def accept(self, password):
        self._delete_from_redis()
        if self.recover:
            recovery_code = None
            user = User.query.filter_by(email=self.email).one()
            user.password_hash = calc_crypt_hash(user.salt, password)
        else:
            recovery_code = generate_random_secret()
            salt = generate_password_salt(app.config['PASSWORD_HASHING_METHOD'])
            user = User(
                email=self.email,
                salt=salt,
                password_hash=calc_crypt_hash(salt, password),
                recovery_code_hash=calc_crypt_hash(salt, recovery_code),
            )
            db.session.add(user)
        db.session.commit()
        self.user_id = user.user_id
        return recovery_code


class HydraLoginRequest:
    BASE_URL = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/login/')
    TIMEOUT = app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']

    def __init__(self, challenge_id):
        self.challenge_id = challenge_id
        self.request_url = self.BASE_URL + challenge_id

    def fetch(self):
        """Return the subject if already logged, `None` otherwise."""

        r = requests.get(self.request_url, timeout=self.TIMEOUT)
        r.raise_for_status()
        fetched_data = r.json()
        return fetched_data['subject'] if fetched_data['skip'] else None

    def accept(self, subject, remember=False, remember_for=0):
        """Approve the request, return an URL to redirect to."""

        r = requests.put(self.request_url + '/accept', timeout=self.TIMEOUT, json={
            'subject': subject,
            'remember': remember,
            'remember_for': remember_for,
        })
        r.raise_for_status()
        return r.json()['redirect_to']


class HydraConsentRequest:
    BASE_URL = urljoin(app.config['HYDRA_ADMIN_URL'], '/oauth2/auth/requests/consent/')
    TIMEOUT = app.config['HYDRA_REQUEST_TIMEOUT_SECONDS']

    def __init__(self, challenge_id):
        self.challenge_id = challenge_id
        self.request_url = self.BASE_URL + challenge_id

    def fetch(self):
        """Return the list of requested scopes, or an empty list if no consent is required."""

        r = requests.get(self.request_url, timeout=self.TIMEOUT)
        r.raise_for_status()
        fetched_data = r.json()
        return [] if fetched_data['skip'] else fetched_data['requested_scope']

    def accept(self, grant_scope, remember=False, remember_for=0):
        """Approve the request, return an URL to redirect to."""

        r = requests.put(self.request_url + '/accept', timeout=self.TIMEOUT, json={
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
    email = request.args.get('email', '')
    is_new_user = 'recover' not in request.args
    if request.method == 'POST':
        captcha_passed, captcha_error_message = verify_captcha(app.config['SHOW_CAPTCHA_ON_SIGNUP'])
        email = request.form['email']
        if is_invalid_email(email):
            flash(gettext('The email address is invalid.'))
        elif not captcha_passed:
            flash(captcha_error_message)
        else:
            computer_code = generate_random_secret()  # to be sent to the user as a login cookie
            user = User.query.filter_by(email=email).one_or_none()
            if user:
                if is_new_user:
                    emails.send_duplicate_registration_email(email)
                else:
                    change_password_request = SignUpRequest.create(email=email, cc=computer_code, recover='yes')
                    emails.send_change_password_email(email, change_password_request.get_link())
            else:
                if is_new_user:
                    register_request = SignUpRequest.create(email=email, cc=computer_code)
                    emails.send_confirm_registration_email(email, register_request.get_link())
                else:
                    # We are asked to change the password of a
                    # non-existing user. In this case we fail
                    # silently, so as not to reveal if the email is
                    # registered or not.
                    pass
            response = redirect(url_for(
                'report_sent_email',
                email=email,
                login_challenge=request.args.get('login_challenge'),
            ))
            response.set_cookie(app.config['COMPUTER_CODE_COOKE_NAME'], computer_code)
            return response

    return render_template(
        'signup.html',
        email=email,
        is_new_user=is_new_user,
        display_captcha=captcha.display_html,
    )


@app.route('/signup/email')
def report_sent_email():
    email = request.args['email']
    return render_template('report_sent_email.html', email=email)


@app.route('/password/<secret>', methods=['GET', 'POST'])
def choose_password(secret):
    signup_request = SignUpRequest.from_secret(secret)
    if not signup_request:
        abort(404)
    require_recovery_code = signup_request.recover and app.config['USE_RECOVERY_CODE']

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
        elif require_recovery_code and not signup_request.verify_recovery_code(recovery_code):
            flash(gettext('Incorrect recovery code.'))
        else:
            recovery_code = signup_request.accept(password)
            redis_users.sadd('cc:' + str(signup_request.user_id), signup_request.cc)  # TODO: use a function
            return recovery_code or 'ok'

    return render_template('choose_password.html', require_recovery_code=require_recovery_code)


@app.route('/signup/success')
def report_signup_success():
    return "/signup/success"


@app.route('/login', methods=['GET', 'POST'])
def login():
    login_request = HydraLoginRequest(request.args['login_challenge'])
    subject = login_request.fetch()
    if subject:
        return redirect(login_request.accept(subject))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).one_or_none()
        if user and user.password_hash == calc_crypt_hash(user.salt, password):
            user_id = user.user_id
            subject = 'user:{}'.format(user_id)
            computer_code = request.cookies.get(app.config['COMPUTER_CODE_COOKE_NAME'], '*')
            if redis_users.sismember('cc:' + str(user_id), computer_code):
                return redirect(login_request.accept(subject))
            else:
                secret = generate_random_secret()
                verification_code = create_login_verification_code(secret, user_id, login_request.challenge_id)
                change_password_page = urljoin(request.host_url, url_for('signup', email=email, recover='true'))
                emails.send_verification_code_email(email, verification_code, change_password_page)
                return redirect(
                    url_for('enter_verification_code',
                            secret=secret,
                            login_challenge=login_request.challenge_id)
                )
        flash(gettext('Incorrect email or password.'))

    return render_template('login.html')


@app.route('/login/<secret>', methods=['GET', 'POST'])
def enter_verification_code(secret):
    vcode_key = 'vcode:' + secret
    user_id, verification_code, challenge_id = redis_users.hmget(vcode_key, ['id', 'code', 'chal'])
    if user_id is None:
        abort(404)  # invalid code verification link

    if request.method == 'POST':
        if verification_code != request.form['verification_code']:
            # TODO: mark a failure in redis.
            flash(gettext('Invalid verification code.'))
        else:
            computer_code = generate_random_secret()
            redis_users.sadd('cc:' + str(user_id), computer_code)  # TODO: use a function
            subject = 'user:{}'.format(user_id)
            login_request = HydraLoginRequest(challenge_id)
            response = redirect(login_request.accept(subject))
            response.set_cookie(app.config['COMPUTER_CODE_COOKE_NAME'], computer_code)
            return response

    return render_template('enter_verification_code.html')


@app.route('/consent', methods=['GET', 'POST'])
def consent():
    consent_request = HydraConsentRequest(request.args['consent_challenge'])
    requested_scope = consent_request.fetch()
    if not requested_scope:
        return redirect(consent_request.accept(requested_scope))

    # TODO: show UI.
    return redirect(consent_request.accept(requested_scope))
